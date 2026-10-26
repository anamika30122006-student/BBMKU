# Binod Bihari Mahto Koyalanchal University (BBMKU)
## University File Management System (UFMS)

A secure, database-backed administrative University File Management System (UFMS) built for **Binod Bihari Mahto Koyalanchal University (BBMKU)**, Dhanbad, Jharkhand.

The system is custom-tailored for university administrators, the Hon'ble Vice-Chancellor, the Registrar, and **EC Sir (Executive Council)**. It provides immediate, crystal-clear visibility into where every file is located, which officer currently has custody, how many days it has been pending, what actions have been recorded on its green sheet, and whether it has been approved, rejected, returned for correction, closed, or permanently archived.

---

## 1. Technology Stack

- **Backend**: Python 3.13+ with Flask
- **Database**: PostgreSQL (with SQLAlchemy ORM & Flask-Migrate / Alembic)
- **Authentication**: Flask-Login with secure password hashing (`werkzeug.security`)
- **Forms & CSRF**: Flask-WTF with CSRF protection
- **Frontend**: HTML5, Vanilla CSS3, and Vanilla JavaScript (No React, Next.js, or Node.js)
- **Document Handling**: Secure server-side validation and storage

---

## 2. University Branding & Identity

- **Official Name**: Binod Bihari Mahto Koyalanchal University (BBMKU)
- **Headquarters**: Dhanbad, Jharkhand, India
- **University Motto**: *ज्ञानं विज्ञान सहितम्* (Knowledge accompanied with Wisdom)
- **Palette**: Administrative Navy Blue (`#0f2a4a`), Crisp White, and Subtle Gold (`#d97706` / `#f59e0b`)
- **Official Logo**: Embedded SVG seal placeholder with clear identification and seamless drop-in support for official seal files (`app/static/images/logo_placeholder.svg`).

---

## 3. Core Modules (Main Navigation)

1. **Dashboard**: Executive monitoring dashboard with real-time counters, pending files list, overdue alerts, department summaries, and recent sanctions.
2. **All Files**: Universal file search, filters (department, category, status, priority, confidentiality, pending duration), sorting, and pagination.
3. **Create New File**: File registration with auto-generated unique numbering (`BBMKU/{DEPT}/{YEAR}/{SEQ}`), metadata, and initial green-sheet noting.
4. **My Assigned Files**: Dedicated inbox of files currently lying on the logged-in officer's desk.
5. **File Movement & Tracking**: Comprehensive movement register recording dispatches, physical peon book references, transfers, and receipts.
6. **Pending Files**: SLA duration tracker with filters for *Today*, *>3 Days*, *>7 Days (Critical)*, *>15 Days*, and *Overdue Files*.
7. **Approval & Decisions**: Registry of all formal approvals, sanctions, and rejections with recorded reasons.
8. **Returned Files**: Query and objection repository for files returned for correction with detailed rectification directives.
9. **Closed Files**: Completed university files repository.
10. **Archive**: Central university archival record room with rack and shelf locator.
11. **Departments & Sections**: Administrative setup of university branches, cells, and faculties.
12. **Officers & Users**: Role-based access control (RBAC) and officer directory.
13. **Reports**: 10 analytical reports with one-click live CSV exports.
14. **Notifications**: In-application alert center for new assignments, forwardings, receipts, approvals, returns, and overdue files.
15. **Audit Logs**: Immutable compliance trail capturing timestamp, user, action, state transition, file reference, and IP address.
16. **Settings**: Configurable turnaround SLA thresholds (warning days, critical days, overdue threshold days) and university identity parameters.

---

## 4. Default Seed Accounts

The database comes pre-seeded with realistic BBMKU administrative accounts:

| Role | Username | Password | Full Name / Office |
| :--- | :--- | :--- | :--- |
| **EC Sir (Executive Viewer)** | `ec_sir` | `Password@123` | Hon'ble Member, Executive Council |
| **System Administrator** | `admin` | `Admin@123` | System Administrator (UFMS Cell) |
| **Vice-Chancellor** | `vc_bbmku` | `Password@123` | Prof. Dr. J. P. Sharma (VC) |
| **Registrar** | `registrar` | `Password@123` | Dr. K. K. Sinha (Registrar) |
| **Finance Officer** | `fo_bbmku` | `Password@123` | Dr. A. K. Choudhary (FO) |
| **Controller of Examinations** | `coe_bbmku` | `Password@123` | Dr. S. N. Singh (COE) |
| **Dean Students' Welfare** | `dsw_bbmku` | `Password@123` | Prof. P. Mahato (DSW) |
| **Section Officer (Estb)** | `so_establishment` | `Password@123` | Sri S. K. Verma (SO Establishment) |
| **Section Officer (Accounts)**| `so_accounts` | `Password@123` | Smt. R. Kumari (SO Accounts) |
| **Dealing Assistant** | `da_admin` | `Password@123` | Shri A. K. Singh (DA General) |

---

## 5. PostgreSQL Database Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- PostgreSQL Server (tested on PostgreSQL 18)

### Step 1: Create PostgreSQL Database
Run PostgreSQL interactive shell or SQL command:
```sql
CREATE DATABASE bbmku_ufms;
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and verify your database credentials:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=bbmku-ufms-secure-production-key
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/bbmku_ufms
```

### Step 3: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Database Seed Script
Populate initial roles, departments, sections, officers, system settings, and sample university files:
```powershell
python seed.py
```

### Step 5: Start Development Server
```powershell
python run.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 6. Running Automated Tests

Run the complete test suite verifying authentication, RBAC permissions, file movements, delay tracking, and CSV exports:
```powershell
python -m pytest -v
```

---

## 7. Project Folder Structure

```
BBMKU File management/
├── app/
│   ├── __init__.py           # Flask application factory, Jinja filters, error handlers
│   ├── config.py             # Config environments (Development, Testing, Production)
│   ├── extensions.py         # SQLAlchemy, LoginManager, CSRFProtect, Migrate
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User, Role, Permission, role_permissions
│   │   ├── department.py     # Department, Section
│   │   ├── file.py           # FileRecord, FileDocument, FileNote, FileMovement, FileDecision
│   │   ├── workflow.py       # WorkflowDefinition, WorkflowStep
│   │   ├── notification.py   # Notification
│   │   ├── audit.py          # AuditLog
│   │   └── setting.py        # SystemSetting
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── auth.py           # LoginForm, ChangePasswordForm
│   │   ├── file.py           # FileCreateForm, FileMovementForm, Decisions, Filters
│   │   └── admin.py          # UserForm, DepartmentForm, SectionForm, SettingForm
│   ├── routes/
│   │   ├── __init__.py       # Blueprint registry
│   │   ├── auth.py           # Authentication routes
│   │   ├── dashboard.py      # EC Sir & Leadership Dashboard
│   │   ├── files.py          # All Files, Create File, File Details, Notings
│   │   ├── workflow.py       # Forward, Receive, Approve, Reject, Return, Close, Archive
│   │   ├── tracking.py       # Movement Register, My Files, Pending Files
│   │   ├── workflow_views.py # Decisions, Returned, Closed, Archive views
│   │   ├── reports.py        # 10 Reports + CSV exports
│   │   ├── notifications.py  # In-app notifications
│   │   ├── audit.py          # Audit logs viewer
│   │   └── admin.py          # Departments, Users, SLA Settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py   # Business logic, state transitions, unique numbering
│   │   ├── audit_service.py  # Centralized immutable audit logger
│   │   ├── notification_service.py # In-app notification dispatcher
│   │   └── metrics_service.py # Real-time dashboard KPI & reports calculations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py     # @permission_required, @role_required, @admin_required
│   │   └── file_storage.py   # Safe file upload/download handler
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Clean administrative navy/gold design system
│   │   ├── js/
│   │   │   └── app.js        # Vanilla JS: modals, sidebar, confirmations
│   │   └── images/
│   │       └── logo_placeholder.svg # Official university emblem placeholder
│   └── templates/
│       ├── base.html         # Master administrative layout
│       ├── auth/             # Login & profile templates
│       ├── dashboard/        # EC Sir executive dashboard
│       ├── files/            # File list, create, and detail templates
│       ├── tracking/         # Movement and pending templates
│       ├── workflow/         # Decisions, returned, closed, archive
│       ├── reports/          # Reports hub
│       ├── notifications/    # Alert center
│       ├── audit/            # Audit logs
│       ├── admin/            # Departments, users, settings
│       └── errors/           # 403, 404, 500 error pages
├── migrations/               # Alembic database migrations
├── uploads/                  # Secure uploaded documents storage
├── tests/
│   ├── conftest.py           # Pytest fixtures & test database setup
│   ├── test_auth.py          # Authentication tests
│   ├── test_file_movement.py # Movement, receipt, return, decision tests
│   └── test_tracking_and_reports.py # Delay calculation & CSV export tests
├── seed.py                   # Initial university database seeder
├── run.py                    # Server entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .env                      # Local environment configuration
├── .gitignore                # Git exclusions
└── README.md                 # Complete documentation
```

---

## 8. Security & Reliability Highlights

1. **Role-Based Access Control (RBAC)**: Enforced via `@permission_required` and `@role_required` decorators on every protected route.
2. **Transaction Integrity**: All file forwarding, custodian re-assignments, movement history insertions, and notification dispatches occur within managed database transactions.
3. **Prevention of Self-Approval**: Standard university governance rule enforced to prevent officers from sanctioning their own files.
4. **Protected Document Storage**: Uploaded documents are stored outside the public directory with unique UUID filenames and served only through authenticated routes verifying confidentiality clearance.
5. **CSRF Protection**: All form submissions and modal actions require valid CSRF tokens.
6. **Immutable Audit Trail**: Changes to file states, permissions, notings, and user logins are logged with actor details, timestamps, and IP addresses.
