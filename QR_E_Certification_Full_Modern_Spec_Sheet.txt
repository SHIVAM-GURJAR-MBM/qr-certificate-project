PROJECT SPECIFICATION SHEET

QR-Based E-Certification and Verification System

Functional • Technical • UI/UX • Security • Testing

Project type | B.E. CSE Minor Project |

— | — |

Specification version | 1.0 — Implementation baseline |

Primary stack | React.js + Python Flask + SQLite |

Core principle | Issue → QR/PDF → Verify → Revoke |

Prepared from the approved project synopsis. This document defines the
MVP build contract.

Document Control & How to Use This Spec

Item | Decision |

— | — |

Purpose | Single source of truth for product scope, UI styling,
behaviors, architecture, data, APIs, security and acceptance. |

Primary users | Issuer/Administrator, Recipient, Public Verifier. |

MVP boundary | One issuing organization or a small number of authorized
organizations; browser-based responsive web app. |

Implementation rule | If a feature is not listed as MVP scope, treat it
as future work unless the project supervisor approves it. |

Source of truth | This spec is aligned with the QR-Based E-Certification
and Verification System synopsis. |

Important scope decision Blockchain is NOT required for the MVP.
Verification uses a unique, hard-to-guess certificate ID and a
server-side database record. A QR code is a pointer to the verification
page, not proof by itself. |

— |

Contents

-   1.  Product overview, goals and scope
-   2.  Roles and permissions
-   3.  Functional requirements and business rules
-   4.  Information architecture and page-by-page UI specification
-   5.  Design system: fonts, colours, sizes, spacing, borders, shadows
        and states
-   6.  Responsive layout, navigation, header, footer and reusable
        components
-   7.  Certificate template and PDF/QR specifications
-   8.  Workflows and edge cases
-   9.  Technical architecture and folder structure
-   10. Database model and API contract
-   11. Security, privacy, accessibility and performance
-   12. Testing, acceptance criteria, delivery plan and future scope

1. Product Overview

The system helps an authorized issuer create certificate templates,
enter recipients individually or import them in bulk, generate PDF
certificates with unique QR codes, distribute them by email, search
issued records, and let the public verify certificate status online.

1.1 Problem being solved

-   Manual certificate preparation takes time, especially for workshops,
    courses, competitions and internships with many recipients.

-   Separate files and spreadsheets make issued-certificate records
    harder to search and maintain.

-   A verifier may not know whether a PDF was genuinely issued or
    whether the certificate has been revoked.

-   Manual verification by email or phone creates avoidable delays.

1.2 Success goals

-   Issue one certificate or a batch using the same controlled workflow.

-   Create a unique certificate ID and QR verification URL for every
    issued certificate.

-   Return clear Valid, Revoked or Not Found outcomes from the
    database-backed verification page.

-   Keep a searchable issuer record and a basic audit trail for
    issuance/revocation.

-   Make core workflows usable on desktop, tablet and mobile browser
    sizes.

1.3 MVP scope

Included in MVP | Not included in MVP |

— | — |

Issuer login/logout and protected pages | Blockchain integration |

Template create/edit/select and preview | Native Android/iOS apps |

Manual recipient form and CSV/XLSX import | Automatic proof of holder
identity |

Individual and bulk PDF generation | Guarantee that an issuing
organization is legitimate |

Unique certificate ID + QR code | Full W3C/Open Badges credential
implementation |

Public verification and issuer revocation | Multi-tenant enterprise
billing/advanced permissions |

Email delivery, search/filter, basic reports, audit trail | AI
certificate design or LLM features |

2. Roles & Permission Model

Role | Can do | Must not do |

— | — | — |

Issuer / Administrator | Log in; manage templates; add/import
recipients; preview, issue, send, search and revoke certificates;
view/export reports. | Access protected actions without authentication;
view other issuers’ data unless explicitly authorized. |

Recipient | Receive an email; open/download own certificate; share
certificate/verification URL. | Access issuer dashboard by default. |

Public verifier | Open a QR URL or enter certificate ID; see status and
approved certificate details. | See recipient email, internal IDs,
private notes, audit logs or PDF storage paths. |

MVP simplification The first version may use one administrator/issuer
account. Keep the database and code role-ready so additional authorized
issuers can be supported later without rewriting the entire app. |

— |

3. Functional Requirements

ID | Requirement | Priority |

— | — | — |

FR-01 Authentication | Issuer can log in and log out. Protected pages
and API routes reject anonymous requests. | High |

FR-02 Dashboard | Show total issued, valid and revoked counts, recent
issuance activity and quick actions. | High |

FR-03 Template management | Create, edit, view and select templates with
organization, title, placeholders, logo/signature and layout settings. |
High |

FR-04 Template preview | Preview a certificate with sample/recipient
data before issuance. | High |

FR-05 Manual recipient entry | Enter full name and optional metadata;
require email when email delivery is selected. | High |

FR-06 Bulk import | Accept CSV/XLSX, validate columns and rows, detect
duplicates and show row-level errors before issue. | High |

FR-07 Unique certificate ID | Generate a unique, unpredictable public
identifier; never expose sequential database primary keys. | High |

FR-08 PDF generation | Generate one PDF or a batch of PDFs using the
chosen template and recipient details. | High |

FR-09 QR generation | Embed a readable QR code linking to the public
verification URL for that exact certificate. | High |

FR-10 Record keeping | Store template/recipient references, issue
timestamp, status, PDF path and issuer reference. | High |

FR-11 Public verification | Show Valid, Revoked or Not Found and only
approved public details. | High |

FR-12 Revocation | Authorized issuer can revoke a certificate with a
reason; verification must reflect the change immediately on the next
request. | High |

FR-13 Email delivery | Send PDF attachment or download/verification
link; record delivery outcome and allow retry. | Medium |

FR-14 Search/filter | Search by certificate ID, recipient name/email,
date range and status where available. | Medium |

FR-15 Reports/export | Show issuance totals and allow CSV export of
filtered issuer records. | Medium |

FR-16 Audit trail/error handling | Record issue/revoke actions and show
understandable validation, import, PDF, email and unknown-ID errors. |
High |

4. Information Architecture & Page Specification

Use one consistent issuer application shell for all protected pages.
Public verification is a separate, minimal shell and must never expose
the issuer sidebar.

Page | Route | Access | Required content | Behavior |

— | — | — | — | — |

Login | /login | Issuer | Brand mark, title, email/username, password,
show/hide password, submit button, validation and generic failure
message. | Successful login → /dashboard; invalid credentials remain on
page. |

Dashboard | /dashboard | Issuer | Greeting, KPI cards, recent activity,
quick actions: Create Template, Issue Certificate, Import Recipients. |
KPI values come from API; empty state explains first step. |

Templates | /templates | Issuer | Template table/cards, search, status,
Create Template CTA, edit/preview actions. | Empty state includes Create
Template action. |

Create/Edit Template | /templates/new; /templates/:id/edit | Issuer |
Template name, organization, certificate title, body text, placeholders,
logo/signature upload, layout options, save and preview. | Validate
required title/name; show unsaved-changes warning. |

Recipients / Import | /recipients; /recipients/import | Issuer | Manual
form, upload CSV/XLSX, required-column guide, import preview,
valid/invalid row counts, row error download. | Never silently drop
rows; issuer confirms before issuance. |

Issue / Preview | /issue; /issue/preview | Issuer | Template selector,
recipient selection, PDF preview, confirm issue, progress/result
summary. | No certificate marked issued until PDF and database record
are consistently saved. |

Certificates | /certificates | Issuer | Search, filters, table, status
chips, view/download/send/revoke actions. | Paginate results;
destructive revoke action requires confirmation. |

Certificate detail | /certificates/:uid | Issuer | Recipient name,
certificate ID, issue date, template, status, PDF action, email status,
audit history, revoke form. | Private issuer-only details require
authorization. |

Reports | /reports | Issuer | Total issued, status breakdown, date
filters, CSV export. | Clearly label date range and applied filters. |

Public verification | /verify/:uid | Public | Brand/issuer identity,
status icon and text, selected details, issue date, certificate ID,
verification timestamp or explanatory note. | No login required; no
email/private notes/internal DB IDs. |

Not Found / Error | app-wide | All | Clear explanation, recovery action,
retry where useful, support/contact only if configured. | Never show
stack traces or secrets. |

5. Design System — Visual Language

Visual direction: modern, trustworthy, calm and document-oriented. Use a
light neutral background, deep navy text, blue primary actions,
restrained cyan accents, and clear status colours. Avoid gradients
everywhere, excessive glassmorphism, tiny text and over-rounded
controls.

5.1 Brand colours (exact tokens)

Token | HEX | Use | Guidance |

— | — | — | — |

Primary / brand | #2563EB | Main CTA, active nav, links, focus ring |
Use white text on primary buttons. |

Primary hover | #1D4ED8 | Hover/pressed primary actions | Do not change
layout on hover. |

Deep navy | #14213D | Logo text, page titles, sidebar/header |
High-trust visual anchor. |

Accent cyan | #06B6D4 | Small highlights, chart accent, decorative icons
| Use sparingly; not for long text. |

Page background | #F8FAFC | App canvas | Avoid pure white for the entire
application. |

Surface / card | #FFFFFF | Cards, tables, forms, modal panels | Use
subtle border to define edges. |

Primary text | #1F2937 | Body copy, labels, table values | Default text
colour. |

Secondary text | #64748B | Helper text, metadata, placeholders | Do not
use for essential low-contrast text. |

Border | #D8E1EC | Input borders, dividers, card edges | 1px standard
border. |

Success | #15803D | Valid status, success notifications | Pair colour
with icon/text. |

Success background | #F0FDF4 | Success alert/chip background | Avoid
colour-only meaning. |

Warning | #B45309 | Pending, caution, import warnings | Use clear label
and icon. |

Warning background | #FFFBEB | Warning alert background | |

Danger | #B91C1C | Revoked, delete, errors | Destructive action requires
confirmation. |

Danger background | #FEF2F2 | Error/revoked background | |

Info background | #EFF6FF | Info panels, help text | |

5.2 Typography

Element | Font family | Desktop size / weight | Mobile size / weight |
Line height |

— | — | — | — | — |

Display/page title | Inter; fallback system-ui, sans-serif | 28–32 px /
700 | 24–28 px / 700 | 1.2 |

Section heading H2 | Inter; fallback system-ui | 20–24 px / 650–700 |
18–22 px / 650–700 | 1.3 |

Card heading H3 | Inter; fallback system-ui | 16–18 px / 600 | 16 px /
600 | 1.35 |

Body / form text | Inter; fallback system-ui | 14–16 px / 400 | 14–16 px
/ 400 | 1.5 |

Labels | Inter; fallback system-ui | 13–14 px / 600 | 13–14 px / 600 |
1.4 |

Helper / metadata | Inter; fallback system-ui | 12–13 px / 400 | 12–13
px / 400 | 1.45 |

Button | Inter; fallback system-ui | 14 px / 600 | 14 px / 600 | 1.0 |

Certificate ID / code | ui-monospace, SFMono-Regular, Consolas | 12–13
px / 500 | 12 px / 500 | 1.4 |

Font loading: use a locally bundled font or a trusted font source if
internet access is available. Always declare a system fallback. Keep
body copy at 14 px minimum for normal UI use; use 12 px only for
non-critical metadata.

5.3 Spacing scale

Token | Value | Typical use |

— | — | — |

space-1 | 4 px | Icon/text micro-gap |

space-2 | 8 px | Label to field; compact row gap |

space-3 | 12 px | Inside compact components |

space-4 | 16 px | Default component padding/gap |

space-5 | 20 px | Form section spacing |

space-6 | 24 px | Card padding / section gap |

space-8 | 32 px | Major section separation |

space-10 | 40 px | Large page blocks |

space-12 | 48 px | Hero/cover breathing room |

5.4 Shape, borders, elevation and motion

Property | Specification |

— | — |

Input height | 44 px default; 48 px for prominent search or touch-heavy
forms. |

Button height | 44 px minimum; 48 px for primary CTA on mobile. |

Border radius | 6 px small chips/inputs; 10 px buttons; 14 px cards; 16
px large panels; pill only for status chips. |

Border | 1 px solid #D8E1EC; use stronger border on focused/invalid
controls. |

Shadow | Cards: 0 1px 3px rgba(15,23,42,0.06); popovers/modals: 0 12px
32px rgba(15,23,42,0.16). |

Motion | 150–200 ms ease-out for hover/focus/expand; respect
prefers-reduced-motion. |

Iconography | Use one consistent line icon set; 18–20 px for controls
and 20–24 px for page actions. |

Content width | Main content max-width around 1440 px; forms generally
640–760 px; public verification card 560–720 px. |

6. App Shell: Header, Sidebar, Navigation & Footer

6.1 Desktop issuer layout

At widths ≥ 1024 px, use a fixed-width left sidebar and a flexible
content region. Keep the top header aligned with the content region.

Region | Specification |

— | — |

Sidebar | Width 248 px expanded; 76 px collapsed. Background #14213D or
white with navy text. Logo at top; grouped navigation; active item uses
#2563EB tint/left indicator; bottom area has profile and logout. |

Top header | Height 64–72 px; white surface; bottom border. Left:
breadcrumb/page title if needed. Right: help icon (optional),
profile/avatar menu, logout inside profile menu. |

Main content | Padding 32 px desktop, 24 px tablet, 16 px mobile. Page
title and primary CTA share a row where space allows. |

Footer | Issuer app footer is quiet and optional: product name, version,
Help/Privacy links only if implemented. Keep it at the bottom of page
content; do not make it sticky over tables. |

Mobile nav | Replace sidebar with a drawer opened by a 44×44 px menu
button. Close drawer after navigation. Keep page title and primary
action reachable. |

6.2 Navigation items

Group | Item | Icon concept | Route |

— | — | — | — |

Overview | Dashboard | grid/dashboard | /dashboard |

Certificates | All Certificates | file-check | /certificates |

Certificates | Issue Certificate | file-plus | /issue |

Manage | Templates | layout/template | /templates |

Manage | Recipients & Import | users/upload | /recipients |

Insights | Reports | chart-bar | /reports |

Account | Profile / Logout | user / log-out | menu action |

Navigation rules: active state must be based on the current route; icons
must never be the only label in expanded navigation; use tooltips in
collapsed mode; do not show issuer-only links on public verification
pages.

6.3 Public verification page shell

-   No issuer sidebar. Use a simple top bar with product mark and a
    small “Certificate Verification” label.

-   Center the verification result card vertically within a light
    neutral canvas; keep the issuer/organization name visible.

-   Footer may include product name, verification disclaimer and privacy
    link if implemented; do not display internal admin links.

-   The status label must be text plus icon: Valid, Revoked, or Not
    Found. Never communicate status through colour alone.

7. Component-Level UI Specification

Component | Base specification | Interaction/state rules |

— | — | — |

Primary button | Blue fill #2563EB, white 14 px semibold text, 44 px
height, 10 px radius, horizontal padding 16–20 px. | Hover #1D4ED8;
disabled 50% opacity with no pointer; visible keyboard focus. |

Secondary button | White surface, navy text, 1 px border #D8E1EC. |
Hover #F1F5F9; same height as primary beside it. |

Destructive button | Danger red fill or red-outline secondary style. |
Confirm before revocation/deletion; explain impact. |

Text input/select | 44 px height; 14–16 px text; 12–14 px horizontal
padding; 1 px border; 8 px radius. | Focus border blue + 2 px visible
focus ring; invalid border red plus message below. |

Textarea | Minimum 96 px height; resize vertically where appropriate. |
Character guidance for long text fields. |

Checkbox/radio | At least 20×20 px visual target; 8 px label gap. |
Entire label clickable; keyboard accessible. |

Status chip | Compact pill with icon + label; 12–13 px semibold. | Valid
green; Revoked red; Draft/Pending amber/neutral. |

Card | White surface, 1 px border, 14 px radius, 20–24 px padding. | Use
shadow sparingly; avoid nested card-on-card stacks. |

Table | Header 12–13 px semibold, body 14 px, row 52–60 px desktop. |
Mobile becomes horizontal scroll or stacked rows; keep row actions
accessible. |

Toast | Top-right desktop; near top on mobile; icon + message + optional
action. | Success/info auto-dismiss after ~4–6 s; errors stay longer or
require dismissal. |

Modal/dialog | Max width 520–640 px; overlay; clear title, summary,
actions. | Trap focus; Escape closes only if safe; confirm destructive
action. |

Empty state | Small illustration/icon, one-line explanation, one primary
next step. | Explain what the user can do next; never show a blank
table. |

Loading state | Skeleton for content; spinner only for short actions. |
Disable duplicate submission; show progress for bulk generation. |

Pagination | Page size selector if needed, current page and
next/previous controls. | Retain filters when moving between pages. |

8. Page-by-Page Visual & Interaction Details

8.1 Dashboard

-   Top row: page title “Dashboard” and primary CTA “Issue Certificate”.
    Secondary CTA “Create Template”.

-   KPI cards: Total Issued, Valid, Revoked, Emails Failed/Pending (only
    if email tracking is implemented).

-   Each KPI card: 12–13 px label, 28–32 px value, 16–20 px icon,
    optional trend only if meaningful data exists.

-   Recent activity table: recipient, certificate title, issue date,
    status and action. Limit to 5–10 rows with “View all”.

-   First-run empty state: explain the recommended sequence — create a
    template, add recipients, issue certificates.

8.2 Template builder

-   Use a two-column layout on desktop: configuration panel (about 40%)
    and live certificate preview (about 60%). Stack on mobile.

-   Fields: Template Name, Organization Name, Certificate Title, body
    text, recipient-name placeholder, course/event name, issue date,
    logo upload, signature image/name, optional certificate footer.

-   Layout options: landscape/portrait, background asset, text
    alignment, font size preset, logo/signature placement. Keep the
    first version to manageable presets rather than a full drag-and-drop
    editor.

-   Show placeholder chips (e.g. {{recipient_name}},
    {{certificate_title}}, {{issue_date}}, {{certificate_id}},
    {{verification_url}}). Document which placeholders are supported.

-   Actions: Save Draft, Preview, Save Changes. Warn before navigating
    away with unsaved edits.

8.3 Recipient entry and bulk import

-   Manual form: Full Name (required), Email (required only if sending
    email), course/event/achievement fields configured by template,
    optional external reference.

-   Bulk import steps: Download sample CSV → Upload CSV/XLSX →
    Map/confirm columns if needed → Preview validation → Fix/download
    errors → Confirm valid rows → Generate.

-   Allowed formats: .csv and .xlsx only. Set configurable size/row
    limits and display them near the upload control.

-   Import preview columns: Row, Full Name, Email, Validation Result,
    Error Reason. Use text and icon for valid/error states.

-   Duplicate policy: flag duplicates before generation; do not issue
    duplicate certificates silently. Let the issuer remove duplicates or
    explicitly confirm a documented policy.

8.4 Certificate list

-   Toolbar: Search input, status filter, date range, template/course
    filter if available, Export CSV button.

-   Columns: Certificate ID (short display with copy action), Recipient,
    Certificate Title, Issue Date, Status, Email Status, Actions.

-   Actions: View, Download PDF, Send/Resend Email, Revoke. Hide or
    disable actions the user cannot perform.

-   Revoke flow: dialog shows recipient, certificate ID, and a required
    reason; final button labelled “Revoke Certificate”.

-   For large datasets use server-side pagination/filtering. Do not load
    every record into the browser by default.

8.5 Public verification result

-   Show organization name, certificate title, recipient display name,
    issue date, certificate ID and verification status, subject to
    privacy settings.

-   Valid: green status icon + “Certificate is valid” + note that the
    issuer’s database currently recognizes it as valid.

-   Revoked: red status icon + “Certificate has been revoked”; show
    revocation date only if approved for public display.

-   Not found: neutral/error treatment + “We could not find a
    certificate with this ID.” Do not reveal whether another private
    record exists.

-   Add a small disclaimer: verification confirms the status of the
    record in this system; it does not independently verify the
    real-world identity of the presenter.

-   Offer “Print verification” only if useful; do not expose private PDF
    storage paths or internal admin actions.

9. Certificate PDF & QR Design Specification

9.1 PDF page and typography

Property | Specification |

— | — |

Default page | A4 landscape (297 × 210 mm) for formal certificates;
allow portrait only if selected in template. |

Safe margin | At least 12–15 mm from page edges; keep text and QR away
from trim edges. |

Certificate title | 28–36 pt, bold, readable serif or sans-serif
selected consistently by template. |

Recipient name | 24–32 pt, bold; the most visually prominent data field.
|

Body text | 12–16 pt; line spacing around 1.3–1.5; ensure long names
wrap without overlap. |

Metadata | 9–11 pt for certificate ID and issue date; must remain
readable when printed. |

Logo/signature | Preserve aspect ratio; do not stretch uploaded assets;
validate allowed image formats. |

QR code | Aim for 25–32 mm square in the PDF; black modules on white
quiet zone; keep sufficient contrast and test print scan. |

Footer | Organization name, certificate ID and short verification
instruction/URL if space allows. |

Output filename | Safe, sanitized filename such as certificate_.pdf; do
not use raw untrusted input in paths. |

9.2 QR content and verification

-   QR encodes an HTTPS verification URL containing the public
    certificate UID, e.g. https://your-domain.example/verify/.

-   Use a cryptographically secure random UID or sufficiently random
    token; enforce a unique database constraint and regenerate on
    collision.

-   The QR must not contain recipient email, private personal details,
    passwords, or the full certificate record.

-   Verification is database-backed: UID found + status valid → Valid;
    UID found + status revoked → Revoked; UID absent → Not Found.

-   A certificate is not considered issued until its database record and
    generated PDF are saved consistently. Use cleanup/rollback handling
    for partial failures.

-   For a local demo, QR links must use a reachable host/device address.
    A localhost URL scanned on a phone will point to the phone itself
    and will not work unless the service is reachable through an
    appropriate network/deployment URL.

10. Core User Workflows

10.1 Issue one certificate

1.  Issuer logs in and opens Dashboard.

2.  Issuer creates/selects a template.

3.  Issuer enters recipient details and validates the form.

4.  Issuer previews the rendered certificate.

5.  Issuer confirms issuance.

6.  Backend generates certificate UID and verification URL, creates QR,
    generates PDF, and stores the certificate record/file consistently.

7.  UI shows success with certificate ID and actions to
    download/send/view.

8.  Recipient or verifier scans QR and sees current database status.

10.2 Issue in bulk

1.  Issuer selects a template and uploads CSV/XLSX.

2.  Backend validates file type, size, required columns, field formats
    and duplicate rows.

3.  UI shows valid/invalid counts and row-level error reasons.

4.  Issuer downloads error rows or corrects data, then confirms the
    valid batch.

5.  Backend generates each certificate and records per-row
    success/failure.

6.  UI displays a batch summary and email delivery results if email was
    requested.

10.3 Revoke a certificate

1.  Issuer opens certificate detail and selects Revoke.

2.  System asks for confirmation and a reason.

3.  Backend checks issuer permission, updates status to revoked, records
    timestamp/reason and writes an audit event.

4.  The public verification page returns Revoked on the next request.

5.  The system retains the record; revocation is not deletion.

11. Technical Architecture & Stack

Layer | Technology | Responsibility / notes |

— | — | — |

Frontend | React.js, HTML, CSS; React Router; Fetch API or Axios |
Responsive pages, reusable components, client-side form states, API
integration and certificate preview. |

Styling | CSS variables/design tokens; CSS Modules or organized global
styles | Centralize colour, spacing, typography, focus and component
states. Tailwind may be used only if team prefers it; design tokens
still remain the source of truth. |

Backend | Python Flask + Flask Blueprints | REST API, authentication,
authorization, validation, certificate business rules and error
responses. |

Database | SQLite for MVP; PostgreSQL possible later | Users, templates,
recipients, certificates, audit events and email attempts. |

PDF | ReportLab | Generate print-ready PDFs from validated template and
recipient data. |

QR | Python qrcode library | Create QR images for the verification URL.
|

Import | pandas / openpyxl | Parse CSV/XLSX and report row-level
validation errors. |

Email | SMTP using environment-based credentials | Send PDF or a link;
track attempts and errors; never hardcode credentials. |

File storage | Controlled local directory for prototype | Keep PDFs and
uploads outside public static listing; use object storage in a later
deployment if needed. |

Testing | pytest for backend; React Testing Library/Vitest optional |
Unit, integration, permission and end-to-end workflow tests. |

Version control | Git + GitHub | Branching, change history, README,
.env.example and issue/task tracking. |

11.1 Suggested folder structure

qr-e-certification/ ├── frontend/ │ ├── public/ │ └── src/ │ ├── app/ #
router, providers │ ├── components/ # buttons, inputs, tables, modals,
status chips │ ├── layouts/ # IssuerLayout, PublicLayout │ ├── pages/ #
Login, Dashboard, Templates, Certificates, Verify │ ├── features/ #
templates, recipients, certificates, reports │ ├── services/ # API
client and endpoint wrappers │ ├── hooks/ │ ├── styles/ # tokens.css,
global.css │ └── utils/ ├── backend/ │ ├── app.py │ ├── config.py │ ├──
routes/ # auth, templates, recipients, certificates, reports │ ├──
models/ │ ├── services/ # pdf, qr, email, import, audit │ ├── utils/ #
validators, errors, ID generation │ ├── tests/ │ └── requirements.txt
├── instance/ # SQLite database; do not commit production data ├──
generated_certificates/ # private/protected output directory ├──
uploads_tmp/ # temporary validated uploads; clean after processing ├──
tests/ # integration/e2e tests if separate ├── .env.example ├──
.gitignore └── README.md

12. Database Specification

Proposed relational schema. Field names can be adjusted during
implementation, but unique constraints, relationships and status rules
must be preserved.

Table | Suggested fields | Purpose |

— | — | — |

users | id PK; name; email UNIQUE; password_hash; role; is_active;
created_at; updated_at | Issuer accounts. Never store plain-text
passwords. |

templates | id PK; name; organization_name; certificate_title;
body_text; layout_config JSON/text; logo_path; signature_path;
created_by FK; created_at; updated_at | Reusable layout and placeholder
configuration. |

recipients | id PK; full_name; email nullable; external_reference
nullable; created_at | Recipient profile/data used during issuance.
Email required only when sending. |

certificates | id PK; certificate_uid UNIQUE; template_id FK;
recipient_id FK; issue_date; issued_at; status; pdf_path; issued_by FK;
revoked_at nullable; revocation_reason nullable | Certificate lifecycle
and metadata. |

audit_logs | id PK; user_id FK; certificate_id FK nullable; action;
details; created_at | Record issuance, revocation and other important
actions. |

email_logs | id PK; certificate_id FK; recipient_email; attempted_at;
status; error_message nullable | Track email attempts without losing
certificate record on failure. |

import_batches (recommended) | id PK; uploaded_by FK; original_filename;
total_rows; valid_rows; invalid_rows; status; created_at | Track bulk
import validation and result summary. |

12.1 Data rules

-   Use primary keys internally and a separate random public
    certificate_uid for verification.

-   Certificate status must be constrained to a known set such as
    valid/revoked; unknown UID returns not-found.

-   Store timestamps consistently (UTC in backend/database where
    practical; display in the user’s local timezone).

-   Use foreign keys and indexes for certificate_uid, status,
    issue_date, recipient name/email and related foreign keys as
    appropriate.

-   Do not delete a certificate to revoke it; retain its lifecycle
    record and audit trail.

-   Public verification response must be a deliberately limited response
    schema, not a direct serialization of the database model.

13. REST API Contract (Proposed)

Method | Endpoint | Access | Purpose |

— | — | — | — |

POST | /api/auth/login | Issuer | Authenticate and create session/token.
|

POST | /api/auth/logout | Issuer | End session/token. |

GET | /api/dashboard/summary | Issuer | Return KPI counts and recent
activity. |

GET / POST | /api/templates | Issuer | List or create templates. |

GET / PUT | /api/templates/{id} | Issuer | Read or update one template.
|

POST | /api/recipients/import | Issuer | Upload and validate CSV/XLSX;
return row-level results/batch ID. |

POST | /api/certificates | Issuer | Issue one certificate. |

POST | /api/certificates/bulk | Issuer | Issue certificates from a
confirmed valid batch. |

GET | /api/certificates | Issuer | Search/filter/paginate issuer
records. |

GET | /api/certificates/{uid} | Issuer | Read issuer-only certificate
details. |

POST | /api/certificates/{uid}/revoke | Issuer | Revoke with reason and
audit event. |

POST | /api/certificates/{uid}/send-email | Issuer | Send/resend
certificate and log outcome. |

GET | /api/verify/{uid} | Public | Return status and approved public
details only. |

GET | /api/reports/issuance | Issuer | Return summary/export data for
selected date range. |

13.1 Consistent response behavior

-   Use standard HTTP status codes: 200/201 success, 400 validation
    error, 401 unauthenticated, 403 forbidden, 404 not found, 409
    conflict/duplicate, 413 upload too large, 422 invalid row data, 429
    rate limited, 500 unexpected server error.

-   Return a consistent JSON shape, e.g. {“success”: false, “message”:
    “Please correct the highlighted fields.”, “errors”: {“email”:
    “Invalid email format”}}.

-   Never send stack traces, password hashes, SMTP credentials, secret
    keys or private file paths to the client.

-   Document required fields, response schema and access level for each
    endpoint in the README or an API collection.

14. Validation & Business Rules

-   Required fields must be validated on both frontend and backend.
    Frontend validation improves usability; backend validation is
    authoritative.

-   Email syntax is validated when an email is provided or email
    delivery is requested.

-   Uploaded file extension, MIME/content, file size, row count and
    headers are validated; do not trust extension alone.

-   Import errors must identify row number and reason; the system must
    not silently discard invalid rows.

-   Duplicate rows must be flagged before generation; define whether
    duplicates are blocked or explicitly confirmed.

-   A valid certificate requires an existing UID and a valid database
    status.

-   Revocation requires issuer authorization and a reason; revocation
    action must be logged.

-   Email failure must not delete or invalidate a successfully issued
    certificate; allow retry and show the failed attempt.

-   PDF failure must not produce a false success state; clean up partial
    files or mark the attempt failed safely.

-   Use safe filenames and prevent path traversal; uploaded images must
    be size/type checked before processing.

15. Security, Privacy & Accessibility

15.1 Security checklist

-   Hash passwords with a reputable password-hashing library; never
    store plain-text passwords.

-   Protect every issuer-only API route with authentication and
    authorization checks.

-   Keep SECRET_KEY, SMTP credentials and deployment secrets in
    environment variables; commit only .env.example.

-   Use HTTPS in deployment; set secure cookie/session settings if
    cookie-based auth is used.

-   Use unpredictable certificate UIDs and enforce a database uniqueness
    constraint.

-   Rate-limit login and public verification endpoints where feasible;
    consider CAPTCHA only if abuse becomes a concern.

-   Restrict upload formats and sizes; sanitize names; store generated
    PDFs outside public directory listing.

-   Avoid exposing recipient email and internal audit details on public
    verification pages.

-   Log important events but never log passwords, tokens or secrets.

-   Use CSRF protection if cookie-based sessions and cross-site form
    submissions are relevant; configure CORS narrowly.

15.2 Accessibility requirements

-   Target WCAG 2.2 AA principles for core flows: text contrast,
    keyboard operation, focus visibility and understandable labels.

-   Every form control has a visible label; placeholders are examples,
    not replacements for labels.

-   All actions can be reached and operated with keyboard; focus order
    follows visual order.

-   Status is communicated through text/icon plus colour, never colour
    alone.

-   Images/logos have appropriate alt text; decorative icons are hidden
    from screen readers where appropriate.

-   Use semantic headings, buttons, links, table headers and descriptive
    validation messages.

-   Respect reduced-motion preferences and do not use flashing effects.

15.3 Privacy

-   Only collect recipient data needed for certificate issuance and
    email delivery.

-   Public verification displays only the fields approved by the
    issuer/project requirements.

-   Protect downloaded PDFs and admin exports; do not expose them
    through guessable public paths.

-   Provide a short privacy note explaining what verification
    information is publicly visible.

16. Responsive & Performance Requirements

Viewport | Layout behavior |

— | — |

Mobile: < 640 px | Single column; drawer navigation; forms full width;
buttons at least 44 px high; tables horizontally scroll or use stacked
record cards; verification card fits screen with 16 px margins. |

Tablet: 640–1023 px | Collapsible navigation; 2-column KPI cards;
template editor stacks or uses compact split view; comfortable 20–24 px
page padding. |

Desktop: ≥ 1024 px | Sidebar + header shell; 3–4 KPI cards per row;
tables show full useful columns; template builder split view. |

-   Show loading/progress for bulk import and generation; do not freeze
    the UI for long jobs.

-   Paginate/search large certificate lists on the server side.

-   Generate PDF/QR on the backend so the final output is consistent and
    not dependent on the client device.

-   Use optimized logos/images and avoid unnecessarily large upload
    payloads.

-   For the demo target, the app should handle a modest batch (for
    example, 100 demo recipients) with clear progress and per-record
    outcomes; tune based on the available machine.

17. Error, Empty, Loading & Success States

Scenario | Required UI behavior |

— | — |

No templates yet | Explain that a template is needed before issuance;
show “Create Template” CTA. |

No certificates yet | Show a useful empty state with “Issue Certificate”
and “Import Recipients” actions. |

Invalid login | Use a generic message such as “Email or password is
incorrect”; do not reveal which part matched. |

Invalid upload | Explain accepted formats/limits and how to fix the
file. |

Some invalid import rows | Show valid/invalid counts, row number, reason
and downloadable error report. |

Generation in progress | Disable duplicate submit, show progress and
tell user not to close the page if required. |

Partial batch failure | Show success/failure totals and let issuer
inspect failed items; do not report all rows as successful. |

Email failed | Keep certificate issued; show failed email status and
retry action. |

Unknown certificate ID | Show “Certificate not found” with a simple
explanation and no internal error. |

Network/server failure | Show retry option where safe; do not clear
unsaved form content unnecessarily. |

Revocation | Confirm with certificate details and required reason; show
success only after server confirms. |

18. Testing Strategy

Area | Test cases | Expected result |

— | — | — |

Authentication | Correct/wrong credentials; anonymous protected request;
inactive user if implemented. | Valid login succeeds; invalid login
fails; protected routes reject anonymous users. |

Template | Create valid template; missing title; invalid image; long
title/name. | Validation shown; saved template previews without
overlapping text. |

Recipient | Missing full name; invalid email; optional email when no
send requested. | Required fields enforced; optional data handled
correctly. |

Import | Valid CSV/XLSX; wrong extension; missing column; malformed
email; duplicates; empty file; oversized file. | Correct rows accepted;
invalid rows reported with row number/reason. |

PDF/QR | Generate single and bulk PDFs; long names; QR scan;
inaccessible URL test. | PDF opens; text does not overlap; QR resolves
to matching certificate UID. |

Verification | Valid UID; revoked UID; random UID; inspect returned
fields. | Correct status shown; no private fields or stack traces
exposed. |

Revocation | Revoke valid certificate; attempt without auth; missing
reason. | Authorized action works and is logged; unauthorized action is
rejected. |

Email | Valid SMTP; wrong SMTP; retry failed email. | Outcome is
visible; certificate remains issued if email fails. |

Search/report | Search by name/UID; filter status/date; export filtered
results. | Results match filters and export is usable. |

Responsive/accessibility | Mobile, tablet, desktop; keyboard navigation;
focus; contrast; form labels. | Core flows remain usable at all target
widths and keyboard focus is visible. |

End-to-end | Login → template → recipient/import → issue → PDF/QR →
verify → revoke → verify again. | Full core workflow is repeatable and
documented. |

19. Definition of Done / Acceptance Criteria

-   Issuer can log in and access protected management pages.

-   Issuer can create/select a template and preview it before issuance.

-   Manual recipient entry works; CSV/XLSX import validates rows and
    explains errors.

-   System can generate individual and batch PDFs with unique IDs and QR
    codes.

-   Every QR points to the correct public verification record.

-   Valid, revoked and not-found outcomes are correct.

-   Revocation updates verification status and creates an audit record.

-   Issuer can search/filter certificates and export a basic report.

-   Email outcome is visible and email failure does not lose the issued
    certificate.

-   Public verification does not expose private fields.

-   Core app is responsive and has useful empty, loading, error and
    success states.

-   README setup instructions, .env.example, tests, screenshots and
    project report are delivered.

20. Six-Week Build Plan

Week | Frontend / Integration focus | Backend / Data focus | Milestone |

— | — | — | — |

1 | Requirements, user flows, wireframes, Git setup, design tokens. |
Database schema, architecture, API plan, environment setup. | Approved
spec and task breakdown. |

2 | Login, issuer shell, dashboard skeleton, template form. | Flask
setup, authentication, models and template APIs. | Frontend/backend
connected. |

3 | Recipient form, import preview, validation feedback. | CSV/XLSX
validation, unique IDs, PDF generation. | Individual certificate PDF
works. |

4 | Certificate preview/list/search/report UI. | QR generation, public
verification, revocation. | QR verify/revoke flow works. |

5 | Email UI, batch progress/results, end-to-end polish. | Email
sending, audit log, security/error handling, batch tests. |
Feature-complete MVP. |

6 | Responsive polish, user testing, screenshots and documentation. |
Integration tests, deployment/demo setup and final report support. |
Tested demo and submission package. |

For an individual project, complete the same milestones sequentially.
Prioritize the core issue → PDF/QR → verify → revoke flow before
optional polish.

21. Risks, Assumptions & Future Enhancements

21.1 Risks and assumptions

-   Email delivery depends on correct SMTP configuration and provider
    limits.

-   Online verification requires the web application to be reachable.

-   The MVP trusts the issuer account and database; it does not
    independently prove issuer legitimacy or presenter identity.

-   QR codes can be copied; authenticity depends on the server-side
    record, permissions and operational security.

-   Template customization is intentionally preset-based to fit the
    six-week scope.

-   The prototype uses SQLite and local file storage; production
    deployment may need PostgreSQL and managed object storage.

21.2 Future enhancements (not MVP blockers)

-   PostgreSQL and managed file/object storage for deployment.

-   Multiple organizations and more granular role-based access.

-   Standards-based credentials such as W3C Verifiable Credentials /
    Open Badges if required.

-   Blockchain-backed proof only if a real trust or audit requirement
    justifies it.

-   Certificate expiry, renewal, bulk resend, analytics and scheduled
    reports.

-   Digital signatures or signed manifests after a clear security design
    is agreed.

22. Final Deliverables

-   Working React + Flask responsive web application.

-   Database schema, migrations/setup notes and safe demo data.

-   Template management, manual/bulk recipient entry, PDF/QR generation.

-   Public verification, revocation and audit trail.

-   Email delivery with visible attempt status.

-   Search/filter and basic issuance report/export.

-   Source code repository, README, .env.example and .gitignore.

-   Test cases/results, UI screenshots, project report and final demo
    script.

Implementation priority Build the reliable end-to-end path first: issuer
login → template → recipient → PDF + QR → public verify → revoke →
verify revoked. Then complete bulk import, email, reports and UI polish.
|

— |

Appendix A — CSS Design Tokens (starter)

:root { –color-primary: #2563EB; –color-primary-hover: #1D4ED8;
–color-navy: #14213D; –color-accent: #06B6D4; –color-page: #F8FAFC;
–color-surface: #FFFFFF; –color-text: #1F2937; –color-muted: #64748B;
–color-border: #D8E1EC; –color-success: #15803D; –color-success-bg:
#F0FDF4; –color-warning: #B45309; –color-warning-bg: #FFFBEB;
–color-danger: #B91C1C; –color-danger-bg: #FEF2F2; –radius-sm: 6px;
–radius-md: 10px; –radius-card: 14px; –space-1: 4px; –space-2: 8px;
–space-3: 12px; –space-4: 16px; –space-5: 20px; –space-6: 24px;
–space-8: 32px; –font-sans: “Inter”, system-ui, -apple-system, “Segoe
UI”, sans-serif; –text-body: 15px; –text-label: 14px; –text-meta: 12px;
} * { box-sizing: border-box; } body { margin: 0; font-family:
var(–font-sans); font-size: var(–text-body); line-height: 1.5; color:
var(–color-text); background: var(–color-page); } :focus-visible {
outline: 3px solid rgba(37, 99, 235, .35); outline-offset: 2px; }

Appendix B — Final UI Review Checklist

-   The same font family, colour tokens, spacing scale and button
    heights are used across pages.

-   Header, sidebar/drawer, active navigation and page title patterns
    are consistent.

-   Every page has loading, empty, error and success states where
    applicable.

-   Forms have visible labels, required indicators, helper text and
    inline validation.

-   Tables have clear status chips, row actions, filters and mobile
    behavior.

-   Public verification is visually distinct from the private issuer
    dashboard.

-   Valid/revoked/not-found statuses use icon + text + colour.

-   QR code scans from the exported PDF and opens the matching live
    verification page.

-   No secrets, private files or internal database IDs are exposed
    publicly or committed to GitHub.

-   End-to-end workflow has been tested on desktop and mobile-sized
    viewports.
