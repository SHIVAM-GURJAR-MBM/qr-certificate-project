import csv
import io
import os
import secrets
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from functools import wraps
from pathlib import Path

import pandas as pd
import qrcode
from flask import Flask, g, jsonify, request, send_file, session
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
INSTANCE = Path(os.getenv("INSTANCE_PATH", ROOT / "instance"))
PDF_DIR = Path(os.getenv("PDF_STORAGE_PATH", ROOT / "generated_certificates"))
DB_PATH = Path(os.getenv("DATABASE_PATH", INSTANCE / "certificates.sqlite3"))
INSTANCE.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
is_production = os.getenv("APP_ENV", "development").lower() == "production"
secret_key = os.getenv("SECRET_KEY")
if is_production and not secret_key:
    raise RuntimeError("SECRET_KEY must be configured in production.")
app.secret_key = secret_key or "local-development-key-change-before-deploy"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=is_production,
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)
CORS(app, supports_credentials=True, origins=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(","))


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    db_dir= os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'issuer', is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS templates(id INTEGER PRIMARY KEY, name TEXT NOT NULL, organization_name TEXT NOT NULL, certificate_title TEXT NOT NULL, body_text TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS recipients(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY, certificate_uid TEXT UNIQUE NOT NULL, template_id INTEGER NOT NULL REFERENCES templates(id), recipient_id INTEGER NOT NULL REFERENCES recipients(id), issue_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('valid','revoked')), pdf_path TEXT NOT NULL, issued_by INTEGER NOT NULL REFERENCES users(id), revoked_at TEXT, revocation_reason TEXT);
    CREATE INDEX IF NOT EXISTS idx_certificates_status ON certificates(status);
    CREATE INDEX IF NOT EXISTS idx_certificates_issue_date ON certificates(issue_date);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), certificate_id INTEGER REFERENCES certificates(id), action TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS email_logs(id INTEGER PRIMARY KEY, certificate_id INTEGER NOT NULL REFERENCES certificates(id), recipient_email TEXT NOT NULL, attempted_at TEXT NOT NULL, status TEXT NOT NULL, error_message TEXT);
    CREATE TABLE IF NOT EXISTS import_batches(id INTEGER PRIMARY KEY, uploaded_by INTEGER NOT NULL REFERENCES users(id), original_filename TEXT, total_rows INTEGER NOT NULL, valid_rows INTEGER NOT NULL, invalid_rows INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
    """)
    if not conn.execute("SELECT id FROM users LIMIT 1").fetchone():
        conn.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)", (os.getenv("ADMIN_NAME", "Certificate Administrator"), os.getenv("ADMIN_EMAIL", "admin@example.com").lower(), generate_password_hash(os.getenv("ADMIN_PASSWORD", "ChangeMe123!")), now()))
    conn.commit()
    conn.close()


def api_error(message, status=400, errors=None):
    return jsonify(success=False, message=message, errors=errors or {}), status


def issuer_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return api_error("Please log in to continue.", 401)
        return fn(*args, **kwargs)
    return wrapped


def audit(user_id, cert_id, action, details=""):
    db().execute("INSERT INTO audit_logs(user_id,certificate_id,action,details,created_at) VALUES(?,?,?,?,?)", (user_id, cert_id, action, details, now()))


def create_pdf(cert_uid, recipient, template, issue_date):
    path = PDF_DIR / f"{cert_uid}.pdf"
    public_base_url = os.getenv("PUBLIC_BASE_URL", request.host_url.rstrip("/")).rstrip("/")
    verify_url = f"{public_base_url}/verify/{cert_uid}"
    page = landscape(A4)
    c = canvas.Canvas(str(path), pagesize=page)
    width, height = page
    c.setFillColor(colors.HexColor("#14213D")); c.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#2563EB")); c.setLineWidth(2); c.roundRect(15*mm, 15*mm, width-30*mm, height-36*mm, 4*mm, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#64748B")); c.setFont("Helvetica", 12); c.drawCentredString(width/2, height-42*mm, template["organization_name"])
    c.setFillColor(colors.HexColor("#14213D")); c.setFont("Helvetica-Bold", 30); c.drawCentredString(width/2, height-65*mm, template["certificate_title"])
    c.setFillColor(colors.HexColor("#475569")); c.setFont("Helvetica", 14); c.drawCentredString(width/2, height-83*mm, "This certificate is proudly presented to")
    c.setFillColor(colors.HexColor("#2563EB")); c.setFont("Helvetica-Bold", 28); c.drawCentredString(width/2, height-103*mm, recipient["full_name"][:55])
    c.setFillColor(colors.HexColor("#334155")); c.setFont("Helvetica", 13)
    text = c.beginText(35*mm, height-119*mm); text.setLeading(19)
    for line in template["body_text"].replace("{name}", recipient["full_name"]).replace("{organization}", template["organization_name"]).splitlines()[:3]: text.textLine(line[:110])
    c.drawText(text)
    c.setFillColor(colors.HexColor("#64748B")); c.setFont("Helvetica", 10); c.drawString(30*mm, 29*mm, f"Issued {issue_date[:10]}  •  ID {cert_uid}")
    qr = qrcode.make(verify_url); qr_path = str(path.with_suffix(".png")); qr.save(qr_path); c.drawImage(qr_path, width-52*mm, 24*mm, 25*mm, 25*mm); os.remove(qr_path)
    c.setFont("Helvetica", 8); c.drawCentredString(width-39.5*mm, 19*mm, "Scan to verify")
    c.save()
    return str(path)


def issue_one(data, user_id):
    name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip().lower() or None
    try: template_id = int(data.get("template_id"))
    except (TypeError, ValueError): template_id = 0
    if not name: return None, "Full name is required."
    if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]): return None, "Enter a valid email address."
    template = db().execute("SELECT * FROM templates WHERE id=?", (template_id,)).fetchone()
    if not template: return None, "Select a valid certificate template."
    uid = secrets.token_urlsafe(18)
    issue_date = now()
    recipient_id = db().execute("INSERT INTO recipients(full_name,email,created_at) VALUES(?,?,?)", (name, email, issue_date)).lastrowid
    recipient = {"full_name": name}
    try:
        pdf_path = create_pdf(uid, recipient, template, issue_date)
        cert_id = db().execute("INSERT INTO certificates(certificate_uid,template_id,recipient_id,issue_date,status,pdf_path,issued_by) VALUES(?,?,?,?,?,?,?)", (uid, template_id, recipient_id, issue_date, "valid", pdf_path, user_id)).lastrowid
        audit(user_id, cert_id, "issued", f"Issued to {name}")
        db().commit()
    except Exception:
        db().rollback()
        (PDF_DIR / f"{uid}.pdf").unlink(missing_ok=True)
        raise
    return {"certificate_uid": uid, "full_name": name, "email": email, "issue_date": issue_date, "status": "valid"}, None


@app.get("/api/health")
def health(): return jsonify(success=True, status="ok")


@app.get("/")
def frontend_index():
    index_path = ROOT / "frontend" / "dist" / "index.html"
    if not index_path.is_file():
        return jsonify(success=False, message="Frontend build is missing. Build frontend/dist before serving the application."), 404
    return send_file(index_path)


@app.get("/<path:asset_path>")
def frontend_assets(asset_path):
    # Keep application endpoints and public verification routed to Flask.
    if asset_path == "api" or asset_path.startswith("api/") or asset_path == "verify" or asset_path.startswith("verify/"):
        return api_error("Not found.", 404)
    dist_dir = ROOT / "frontend" / "dist"
    candidate = (dist_dir / asset_path).resolve()
    if not candidate.is_relative_to(dist_dir.resolve()) or not candidate.is_file():
        return send_file(dist_dir / "index.html") if (dist_dir / "index.html").is_file() else api_error("Frontend build is missing.", 404)
    return send_file(candidate)


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower(); password = str(data.get("password", ""))
    user = db().execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password): return api_error("Email or password is incorrect.", 401)
    session.clear(); session["user_id"] = user["id"]; session["user_name"] = user["name"]
    return jsonify(success=True, user={"name": user["name"], "email": user["email"]})


@app.post("/api/auth/logout")
def logout(): session.clear(); return jsonify(success=True)


@app.get("/api/auth/me")
def me():
    if not session.get("user_id"): return api_error("Not logged in.", 401)
    return jsonify(success=True, user={"name": session.get("user_name")})


@app.get("/api/dashboard/summary")
@issuer_required
def summary():
    conn = db(); total = conn.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]
    valid = conn.execute("SELECT COUNT(*) FROM certificates WHERE status='valid'").fetchone()[0]
    revoked = total-valid
    recent = conn.execute("SELECT c.certificate_uid,c.issue_date,c.status,r.full_name,t.certificate_title FROM certificates c JOIN recipients r ON r.id=c.recipient_id JOIN templates t ON t.id=c.template_id ORDER BY c.id DESC LIMIT 6").fetchall()
    return jsonify(success=True, total=total, valid=valid, revoked=revoked, recent=[dict(r) for r in recent])


@app.route("/api/templates", methods=["GET", "POST"])
@issuer_required
def templates():
    if request.method == "GET": return jsonify(success=True, templates=[dict(x) for x in db().execute("SELECT * FROM templates ORDER BY id DESC")])
    data=request.get_json(silent=True) or {}; name=str(data.get("name", "")).strip(); org=str(data.get("organization_name", "")).strip(); title=str(data.get("certificate_title", "")).strip(); body=str(data.get("body_text", "")).strip()
    errors={k:"This field is required." for k,v in (("name",name),("organization_name",org),("certificate_title",title),("body_text",body)) if not v}
    if errors: return api_error("Please complete the required fields.", 400, errors)
    cur=db().execute("INSERT INTO templates(name,organization_name,certificate_title,body_text,created_at,updated_at) VALUES(?,?,?,?,?,?)",(name,org,title,body,now(),now())); db().commit()
    return jsonify(success=True, template=dict(db().execute("SELECT * FROM templates WHERE id=?",(cur.lastrowid,)).fetchone())),201


@app.put("/api/templates/<int:template_id>")
@issuer_required
def update_template(template_id):
    data=request.get_json(silent=True) or {}; fields=[str(data.get(k,"")).strip() for k in ("name","organization_name","certificate_title","body_text")]
    if not all(fields): return api_error("All template fields are required.")
    cur=db().execute("UPDATE templates SET name=?,organization_name=?,certificate_title=?,body_text=?,updated_at=? WHERE id=?",(*fields,now(),template_id)); db().commit()
    if not cur.rowcount:return api_error("Template not found.",404)
    return jsonify(success=True)


@app.post("/api/certificates")
@issuer_required
def issue_certificate():
    data=request.get_json(silent=True) or {}; cert,error=issue_one(data,session["user_id"])
    if error:return api_error(error)
    return jsonify(success=True,certificate=cert),201


@app.get("/api/certificates")
@issuer_required
def certificates():
    search=request.args.get("q","").strip(); status=request.args.get("status","").strip()
    sql="SELECT c.certificate_uid,c.issue_date,c.status,c.revoked_at,c.revocation_reason,r.full_name,r.email,t.certificate_title,t.organization_name FROM certificates c JOIN recipients r ON r.id=c.recipient_id JOIN templates t ON t.id=c.template_id WHERE 1=1"; args=[]
    if search: sql+=" AND (c.certificate_uid LIKE ? OR r.full_name LIKE ? OR COALESCE(r.email,'') LIKE ?)"; args += [f"%{search}%"]*3
    if status in ("valid","revoked"): sql+=" AND c.status=?";args.append(status)
    sql+=" ORDER BY c.id DESC LIMIT 200"
    return jsonify(success=True,certificates=[dict(x) for x in db().execute(sql,args)])


@app.get("/api/certificates/<uid>")
@issuer_required
def certificate_detail(uid):
    row=db().execute("SELECT c.*,r.full_name,r.email,t.name AS template_name,t.certificate_title,t.organization_name FROM certificates c JOIN recipients r ON r.id=c.recipient_id JOIN templates t ON t.id=c.template_id WHERE c.certificate_uid=?",(uid,)).fetchone()
    if not row:return api_error("Certificate not found.",404)
    result={k:row[k] for k in row.keys() if k!="pdf_path"}
    result["audit"]= [dict(x) for x in db().execute("SELECT action,details,created_at FROM audit_logs WHERE certificate_id=? ORDER BY id DESC",(row["id"],))]
    return jsonify(success=True,certificate=result)


@app.get("/api/certificates/<uid>/pdf")
@issuer_required
def download_pdf(uid):
    row=db().execute("SELECT pdf_path FROM certificates WHERE certificate_uid=?",(uid,)).fetchone()
    if not row or not Path(row["pdf_path"]).is_file():return api_error("Certificate PDF not found.",404)
    return send_file(row["pdf_path"],as_attachment=True,download_name=f"certificate-{uid}.pdf",mimetype="application/pdf")


@app.post("/api/certificates/<uid>/revoke")
@issuer_required
def revoke(uid):
    data=request.get_json(silent=True) or {}; reason=str(data.get("reason","")).strip()
    if not reason:return api_error("A revocation reason is required.",400,{"reason":"Enter a reason for revocation."})
    row=db().execute("SELECT id,status FROM certificates WHERE certificate_uid=?",(uid,)).fetchone()
    if not row:return api_error("Certificate not found.",404)
    if row["status"]=="revoked":return api_error("This certificate has already been revoked.",409)
    db().execute("UPDATE certificates SET status='revoked',revoked_at=?,revocation_reason=? WHERE id=?",(now(),reason,row["id"]));audit(session["user_id"],row["id"],"revoked",reason);db().commit()
    return jsonify(success=True,message="Certificate revoked.")


@app.get("/api/verify/<uid>")
def verify(uid):
    row=db().execute("SELECT c.certificate_uid,c.issue_date,c.status,c.revoked_at,r.full_name,t.certificate_title,t.organization_name FROM certificates c JOIN recipients r ON r.id=c.recipient_id JOIN templates t ON t.id=c.template_id WHERE c.certificate_uid=?",(uid,)).fetchone()
    if not row:return jsonify(success=True,found=False,status="not_found",message="Certificate not found.")
    return jsonify(success=True,found=True,certificate={k:row[k] for k in row.keys()},verified_at=now())


@app.post("/api/recipients/import")
@issuer_required
def import_recipients():
    file=request.files.get("file")
    if not file:return api_error("Choose a CSV or XLSX file.")
    suffix=Path(file.filename or "").suffix.lower()
    if suffix not in (".csv",".xlsx"):return api_error("Only CSV and XLSX files are supported.")
    try:
        content=file.read()
        frame=pd.read_csv(io.BytesIO(content)) if suffix==".csv" else pd.read_excel(io.BytesIO(content),engine="openpyxl")
    except Exception:return api_error("We could not read this file. Check its format and try again.")
    frame.columns=[str(c).strip().lower().replace(" ","_") for c in frame.columns]
    if "full_name" not in frame.columns:return api_error("The file must include a full_name column.",422,{"columns":"Required column: full_name"})
    valid=[]; errors=[]; seen=set()
    for index,row in frame.iterrows():
        line=index+2; name=str(row.get("full_name","")).strip(); email=str(row.get("email","")).strip()
        if email.lower() in ("nan","none"):email=""
        if not name or name.lower()=="nan":errors.append({"row":line,"reason":"Full name is required."});continue
        key=(name.lower(),email.lower())
        if key in seen:errors.append({"row":line,"reason":"Duplicate recipient row."});continue
        seen.add(key)
        if email and ("@" not in email or "." not in email.rsplit("@",1)[-1]):errors.append({"row":line,"reason":"Invalid email address."});continue
        valid.append({"full_name":name,"email":email or None})
    cur=db().execute("INSERT INTO import_batches(uploaded_by,original_filename,total_rows,valid_rows,invalid_rows,status,created_at) VALUES(?,?,?,?,?,?,?)",(session["user_id"],Path(file.filename).name,len(frame),len(valid),len(errors),"validated",now()));db().commit()
    return jsonify(success=True,batch_id=cur.lastrowid,total_rows=len(frame),valid_rows=valid,invalid_rows=errors),200


@app.post("/api/certificates/bulk")
@issuer_required
def issue_bulk():
    data=request.get_json(silent=True) or {}; template_id=data.get("template_id"); recipients=data.get("recipients",[])
    if not isinstance(recipients,list) or not recipients:return api_error("Add at least one valid recipient.")
    if len(recipients)>100:return api_error("A batch can contain at most 100 recipients.",413)
    results=[]
    for item in recipients:
        cert,error=issue_one({**item,"template_id":template_id},session["user_id"])
        results.append({"success":not bool(error),**(cert or {}),**({"error":error,"full_name":item.get("full_name","")} if error else {})})
    return jsonify(success=True,issued=sum(1 for x in results if x["success"]),failed=sum(1 for x in results if not x["success"]),results=results),201


@app.post("/api/certificates/<uid>/send-email")
@issuer_required
def send_certificate_email(uid):
    row=db().execute("SELECT c.id,c.pdf_path,r.email,r.full_name,c.certificate_uid FROM certificates c JOIN recipients r ON r.id=c.recipient_id WHERE c.certificate_uid=?",(uid,)).fetchone()
    if not row:return api_error("Certificate not found.",404)
    data=request.get_json(silent=True) or {}
    if not isinstance(data,dict):return api_error("Request body must be a JSON object.")
    recipient=str(data.get("email",row["email"] or "")).strip()
    if "@" not in recipient:return api_error("A valid recipient email is required.",400,{"email":"Enter a valid email address."})
    smtp_host=os.getenv("SMTP_HOST","").strip(); smtp_from=os.getenv("SMTP_FROM","").strip()
    smtp_username=os.getenv("SMTP_USERNAME","").strip(); smtp_password=os.getenv("SMTP_PASSWORD","")
    if not smtp_host or not smtp_from:return api_error("Email delivery is not configured. Set SMTP_HOST and SMTP_FROM in the backend .env file.",503)
    if bool(smtp_username)!=bool(smtp_password):return api_error("SMTP authentication is incomplete. Set both SMTP_USERNAME and SMTP_PASSWORD, or leave both blank.",503)
    try:
        msg=EmailMessage();msg["Subject"]=f"Your certificate {row['certificate_uid']}";msg["From"]=smtp_from;msg["To"]=recipient
        public_base_url=os.getenv("PUBLIC_BASE_URL",request.host_url.rstrip("/")).rstrip("/")
        msg.set_content(f"Hello {row['full_name']},\n\nYour certificate is attached. Verify it at {public_base_url}/verify/{row['certificate_uid']}.")
        msg.add_attachment(Path(row["pdf_path"]).read_bytes(),maintype="application",subtype="pdf",filename=f"certificate-{row['certificate_uid']}.pdf")
        smtp_port=int(os.getenv("SMTP_PORT","587"))
        use_ssl=os.getenv("SMTP_USE_SSL","false").strip().lower()=="true"
        smtp_class=smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_class(smtp_host,smtp_port,timeout=15) as smtp:
            if not use_ssl and os.getenv("SMTP_USE_TLS","true").strip().lower()=="true":smtp.starttls()
            if smtp_username:smtp.login(smtp_username,smtp_password)
            smtp.send_message(msg)
        status="sent"; error=None
    except Exception as exc:
        app.logger.exception("Certificate email delivery failed for certificate %s", row["certificate_uid"])
        status="failed";error=str(exc)[:300]
    db().execute("INSERT INTO email_logs(certificate_id,recipient_email,attempted_at,status,error_message) VALUES(?,?,?,?,?)",(row["id"],recipient,now(),status,error));db().commit()
    if status=="failed":return api_error("Certificate was issued, but email delivery failed. Check SMTP settings and retry.",502)
    return jsonify(success=True,message="Certificate email sent.")


@app.get("/api/reports/issuance")
@issuer_required
def report():
    rows=db().execute("SELECT c.certificate_uid,c.issue_date,c.status,r.full_name,r.email,t.certificate_title,t.organization_name FROM certificates c JOIN recipients r ON r.id=c.recipient_id JOIN templates t ON t.id=c.template_id ORDER BY c.id DESC").fetchall()
    if request.args.get("format")=="csv":
        output=io.StringIO();writer=csv.DictWriter(output,fieldnames=["certificate_uid","issue_date","status","full_name","email","certificate_title","organization_name"]);writer.writeheader();writer.writerows([dict(r) for r in rows]);return send_file(io.BytesIO(output.getvalue().encode()),mimetype="text/csv",as_attachment=True,download_name="certificate-report.csv")
    return jsonify(success=True,total=len(rows),valid=sum(x["status"]=="valid" for x in rows),revoked=sum(x["status"]=="revoked" for x in rows))


@app.get("/verify/<uid>")
def verify_page(uid):
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Certificate verification</title><style>*{box-sizing:border-box}body{margin:0;background:#f8fafc;color:#1f2937;font:15px system-ui;min-height:100vh;display:grid;place-items:center;padding:20px}.card{background:white;border:1px solid #d8e1ec;border-radius:16px;padding:36px;max-width:560px;width:100%;box-shadow:0 1px 3px #0f172a10}.brand{color:#14213d;font-weight:700;letter-spacing:.02em}.status{display:inline-flex;padding:7px 12px;border-radius:30px;font-weight:700;margin:20px 0}.valid{color:#15803d;background:#f0fdf4}.revoked{color:#b91c1c;background:#fef2f2}.missing{color:#64748b;background:#f1f5f9}h1{font-size:27px;color:#14213d;margin:12px 0}.name{font-size:22px;font-weight:650}.meta{color:#64748b;font-size:13px}.row{border-top:1px solid #d8e1ec;padding:14px 0}.id{font-family:monospace;overflow-wrap:anywhere}.note{margin-top:24px;color:#64748b;font-size:13px}</style></head><body><main class='card'><div class='brand'>CERTIFICATE CHECK</div><div id='result'>Loading verification…</div><p class='note'>This page displays public certificate details only. Verification reflects the issuer’s current record.</p></main><script>fetch('/api/verify/"""+uid+"""').then(r=>r.json()).then(d=>{const e=document.querySelector('#result');if(!d.found){e.innerHTML='<span class="status missing">NOT FOUND</span><h1>Certificate not found</h1><p class="meta">Check the certificate ID and try again.</p>';return}const c=d.certificate;const ok=c.status==='valid';e.innerHTML='<span class="status '+(ok?'valid':'revoked')+'">'+(ok?'✓ VALID':'! REVOKED')+'</span><h1>'+esc(c.certificate_title)+'</h1><div class="name">'+esc(c.full_name)+'</div><p>'+esc(c.organization_name)+'</p><div class="row"><strong>Certificate ID</strong><div class="id">'+esc(c.certificate_uid)+'</div></div><div class="row"><strong>Issue date</strong><div>'+new Date(c.issue_date).toLocaleDateString()+'</div></div>'+(ok?'':'<div class="row"><strong>Current status</strong><div>This certificate has been revoked.</div></div>')+'<p class="meta">Verified '+new Date(d.verified_at).toLocaleString()+'</p>'}).catch(()=>document.querySelector('#result').textContent='Verification is temporarily unavailable. Please try again.');function esc(v){const x=document.createElement('span');x.textContent=v||'';return x.innerHTML}</script></body></html>""",200,{"Content-Type":"text/html; charset=utf-8"}


init_db()

if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    app.run(host ='0.0.0.0',port=port)
    

