import os
from datetime import datetime, timezone, timedelta, date
from app import create_app
from app.extensions import db
from app.models.user import User, Role, Permission
from app.models.department import Department, Section
from app.models.file import FileRecord, FileMovement, FileDecision, FileNote, FileDocument
from app.models.workflow import WorkflowDefinition, WorkflowStep
from app.models.setting import SystemSetting
from app.services.audit_service import log_audit_event


def seed_database(reset=False):
    app = create_app()
    with app.app_context():
        if reset:
            print("Resetting database tables...")
            db.drop_all()

        print("Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if not reset and Role.query.first():
            print("Database already contains roles. Skipping full reseeding.")
            return

        print("Seeding permissions...")
        all_perms = [
            # Code, Name, Category
            ('view_all_files', 'View All University Files', 'File Management'),
            ('create_file', 'Create and Register New File', 'File Management'),
            ('edit_file', 'Edit File Metadata', 'File Management'),
            ('forward_file', 'Forward File to Next Officer', 'Workflow'),
            ('receive_file', 'Acknowledge File Receipt', 'Workflow'),
            ('return_file', 'Return File for Correction', 'Workflow'),
            ('add_note', 'Add File Noting (Green Sheet)', 'Workflow'),
            ('upload_document', 'Upload Supporting Documents', 'File Management'),
            ('approve_file', 'Sanction and Approve File', 'Decision Authority'),
            ('reject_file', 'Disallow and Reject File', 'Decision Authority'),
            ('close_file', 'Close Completed File', 'Decision Authority'),
            ('archive_file', 'Transfer File to University Archive', 'Archival'),
            ('manage_users', 'Create and Manage Officers & Roles', 'Administration'),
            ('manage_departments', 'Manage Departments and Sections', 'Administration'),
            ('view_reports', 'Access Analytical Reports', 'Reports'),
            ('export_reports', 'Export Data to CSV / Excel', 'Reports'),
            ('view_audit_logs', 'Inspect System Audit Logs', 'Compliance'),
            ('manage_settings', 'Configure System & SLA Settings', 'Administration')
        ]
        
        perm_objs = {}
        for code, name, cat in all_perms:
            p = Permission(code=code, name=name, category=cat)
            db.session.add(p)
            perm_objs[code] = p
        db.session.commit()

        print("Seeding roles...")
        roles_data = {
            'EC_VIEWER': {
                'display_name': 'EC Sir / Executive Council Viewer',
                'description': 'High-level executive viewer for monitoring all university files, movement tracking, and reports',
                'perms': ['view_all_files', 'view_reports', 'export_reports', 'view_audit_logs']
            },
            'SYSTEM_ADMIN': {
                'display_name': 'System Administrator',
                'description': 'Full administrative control over users, workflows, settings, and file registry',
                'perms': list(perm_objs.keys())
            },
            'APPROVING_AUTHORITY': {
                'display_name': 'Approving Authority / Vice-Chancellor',
                'description': 'Supreme sanctioning authority with approval, rejection, closure, and noting privileges',
                'perms': ['view_all_files', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document', 'approve_file', 'reject_file', 'close_file', 'archive_file', 'view_reports', 'export_reports', 'view_audit_logs']
            },
            'REGISTRAR': {
                'display_name': 'Registrar',
                'description': 'Chief Administrative Officer of the University with high-level endorsement and approval authority',
                'perms': ['view_all_files', 'create_file', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document', 'approve_file', 'reject_file', 'close_file', 'view_reports', 'export_reports', 'view_audit_logs']
            },
            'DEPARTMENT_HEAD': {
                'display_name': 'Department Head / Officer In-Charge',
                'description': 'Head of University Department / Dean with file routing, recommendation, and departmental noting authority',
                'perms': ['create_file', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document', 'view_reports']
            },
            'SECTION_OFFICER': {
                'display_name': 'Section Officer (SO)',
                'description': 'Supervises branch operations, scrutinizes proposals, records formal minutes, forwards upwards',
                'perms': ['create_file', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document']
            },
            'DEALING_ASSISTANT': {
                'display_name': 'Dealing Assistant (DA)',
                'description': 'Initiates file processing, records initial notes, collects documents, forwards to SO',
                'perms': ['create_file', 'forward_file', 'receive_file', 'add_note', 'upload_document']
            }
        }

        role_objs = {}
        for r_name, r_info in roles_data.items():
            r = Role(name=r_name, display_name=r_info['display_name'], description=r_info['description'], is_system_role=True)
            for p_code in r_info['perms']:
                r.add_permission(perm_objs[p_code])
            db.session.add(r)
            role_objs[r_name] = r
        db.session.commit()

        print("Seeding 15 official BBMKU departments...")
        depts_data = [
            ('Vice-Chancellor (VC) Secretariat', 'VCO', 'Office of the Hon\'ble Vice-Chancellor', [
                ('Confidential & Cabinet Cell', 'VCO-CAB', 'Cabinet matters and council communications'),
                ('Executive Council Cell', 'VCO-EC', 'Matters placed before Executive Council')
            ]),
            ('Registrar Office', 'REG', 'Central University Administration & Governance', [
                ('Council & Syndicate Section', 'REG-CS', 'University governance & statutory meetings'),
                ('General Administration', 'REG-GA', 'General notifications and liaison')
            ]),
            ('Finance Department', 'FIN', 'Budgeting, Accounting, Audits & Grants', [
                ('Budget & Grants Section', 'FIN-BG', 'State grants, UGC grants, and estimates'),
                ('Salary & Pension Section', 'FIN-SP', 'Payroll, pension, and CPF disbursals')
            ]),
            ('Examination Department', 'EXAM', 'Conduct of Exams, Tabulation & Certifications', [
                ('Confidential Cell', 'EXAM-CONF', 'Question paper setting and moderation'),
                ('Tabulation & Degree Section', 'EXAM-DEG', 'Marksheets, degrees, and convocation lists')
            ]),
            ('Establishment Department', 'ESTB', 'Personnel, Service Matters & Recruitments', [
                ('Teaching Staff Section', 'ESTB-TCH', 'Service records, promotions, and leave of faculty'),
                ('Non-Teaching Staff Section', 'ESTB-NT', 'Staff cadre, confirmations, and welfare')
            ]),
            ('Academic Section', 'ACAD', 'Curriculum, Board of Studies & Academic Councils', [
                ('Curriculum & BoS Cell', 'ACAD-BOS', 'Syllabus revision and NEP implementation')
            ]),
            ('Affiliation Department', 'AFF', 'College Affiliation, Inspections & NOCs', [
                ('College Inspection Cell', 'AFF-INSP', 'Verification of infrastructure and norms')
            ]),
            ('Admission Department', 'ADM', 'University Central Admissions & Enrollment', [
                ('Chancellor Portal Cell', 'ADM-CP', 'State admissions portal management')
            ]),
            ('Colleges / Constituent Colleges', 'COLL', 'Constituent and Affiliated College Matters', [
                ('Principal Liaison Cell', 'COLL-LIA', 'Coordination with college principals')
            ]),
            ('Proctor Section', 'PROC', 'Campus Discipline, Security & Anti-Ragging', [
                ('Discipline & Security Cell', 'PROC-DISC', 'Campus maintenance of order')
            ]),
            ('College Development Council (CCDC)', 'CCDC', 'College Development & Grants', [
                ('College Grants Wing', 'CCDC-GRT', 'UGC and state development assistance')
            ]),
            ('DHW (Department of Higher Education Wing)', 'DHW', 'State Government Liaison & Directives', [
                ('Govt Directives Cell', 'DHW-DIR', 'Higher Education Dept correspondence')
            ]),
            ('IQAC (Internal Quality Assurance Cell)', 'IQAC', 'Accreditation, NAAC & Quality Standards', [
                ('NAAC Data Cell', 'IQAC-NAAC', 'Institutional data and quality metrics')
            ]),
            ('Office State Incharge', 'OSI', 'State Nodal Affairs & Protocol', [
                ('State Protocol Cell', 'OSI-PROT', 'Coordination with state bodies')
            ]),
            ('RUSA (Rashtriya Uchchatar Shiksha Abhiyan)', 'RUSA', 'RUSA Projects, Infrastructure & Funding', [
                ('Project Monitoring Unit', 'RUSA-PMU', 'Central and state funded infrastructure monitoring')
            ])
        ]

        dept_objs = {}
        for d_name, d_code, d_desc, sec_list in depts_data:
            d = Department(name=d_name, code=d_code, description=d_desc)
            db.session.add(d)
            db.session.flush()
            dept_objs[d_code] = d

            for s_name, s_code, s_desc in sec_list:
                s = Section(department_id=d.id, name=s_name, code=s_code, description=s_desc)
                db.session.add(s)
        db.session.commit()

        print("Seeding university officers & users...")
        users_seed = [
            {
                'username': 'ec_sir',
                'email': 'ec.sir@bbmku.ac.in',
                'full_name': 'Hon\'ble Member, Executive Council (EC)',
                'designation': 'Executive Council Member (EC Sir)',
                'phone': '+91 94311 00001',
                'role': 'EC_VIEWER',
                'dept': 'VCO',
                'pwd': 'Password@123'
            },
            {
                'username': 'admin',
                'email': 'admin.ufms@bbmku.ac.in',
                'full_name': 'System Administrator (UFMS Cell)',
                'designation': 'System Administrator',
                'phone': '+91 94311 00002',
                'role': 'SYSTEM_ADMIN',
                'dept': 'REG',
                'pwd': 'Admin@123'
            },
            {
                'username': 'vc_bbmku',
                'email': 'vc@bbmku.ac.in',
                'full_name': 'Prof. Dr. J. P. Sharma',
                'designation': 'Vice-Chancellor, BBMKU',
                'phone': '+91 94311 00003',
                'role': 'APPROVING_AUTHORITY',
                'dept': 'VCO',
                'pwd': 'Password@123'
            },
            {
                'username': 'registrar',
                'email': 'registrar@bbmku.ac.in',
                'full_name': 'Dr. K. K. Sinha',
                'designation': 'Registrar, BBMKU',
                'phone': '+91 94311 00004',
                'role': 'REGISTRAR',
                'dept': 'REG',
                'pwd': 'Password@123'
            },
            {
                'username': 'fo_bbmku',
                'email': 'fo@bbmku.ac.in',
                'full_name': 'Dr. A. K. Choudhary',
                'designation': 'Finance Officer, BBMKU',
                'phone': '+91 94311 00005',
                'role': 'DEPARTMENT_HEAD',
                'dept': 'FIN',
                'pwd': 'Password@123'
            },
            {
                'username': 'coe_bbmku',
                'email': 'coe@bbmku.ac.in',
                'full_name': 'Dr. S. N. Singh',
                'designation': 'Controller of Examinations',
                'phone': '+91 94311 00006',
                'role': 'DEPARTMENT_HEAD',
                'dept': 'EXAM',
                'pwd': 'Password@123'
            },
            {
                'username': 'dsw_bbmku',
                'email': 'dsw@bbmku.ac.in',
                'full_name': 'Prof. P. Mahato',
                'designation': 'In-Charge, Admission & Welfare',
                'phone': '+91 94311 00007',
                'role': 'DEPARTMENT_HEAD',
                'dept': 'ADM',
                'pwd': 'Password@123'
            },
            {
                'username': 'so_establishment',
                'email': 'so.estb@bbmku.ac.in',
                'full_name': 'Sri S. K. Verma',
                'designation': 'Section Officer (Establishment)',
                'phone': '+91 94311 00008',
                'role': 'SECTION_OFFICER',
                'dept': 'ESTB',
                'pwd': 'Password@123'
            },
            {
                'username': 'so_accounts',
                'email': 'so.accounts@bbmku.ac.in',
                'full_name': 'Smt. R. Kumari',
                'designation': 'Section Officer (Accounts)',
                'phone': '+91 94311 00009',
                'role': 'SECTION_OFFICER',
                'dept': 'FIN',
                'pwd': 'Password@123'
            },
            {
                'username': 'da_admin',
                'email': 'da.admin@bbmku.ac.in',
                'full_name': 'Shri A. K. Singh',
                'designation': 'Dealing Assistant (Establishment)',
                'phone': '+91 94311 00010',
                'role': 'DEALING_ASSISTANT',
                'dept': 'ESTB',
                'pwd': 'Password@123'
            }
        ]

        user_objs = {}
        for u in users_seed:
            user = User(
                username=u['username'],
                email=u['email'],
                full_name=u['full_name'],
                designation=u['designation'],
                phone=u['phone'],
                role_id=role_objs[u['role']].id,
                department_id=dept_objs[u['dept']].id if u['dept'] in dept_objs else None,
                is_active=True
            )
            user.set_password(u['pwd'])
            db.session.add(user)
            db.session.flush()
            user_objs[u['username']] = user
        db.session.commit()

        print("Seeding system settings...")
        settings_data = [
            ('SLA_DELAY_WARNING_DAYS', '3', 'Warning threshold in days when file is pending with an officer', 'SLA'),
            ('SLA_DELAY_CRITICAL_DAYS', '7', 'Critical threshold in days when file requires urgent attention', 'SLA'),
            ('SLA_DELAY_OVERDUE_DAYS', '15', 'Default deadline threshold when a file is marked overdue', 'SLA'),
            ('UNIVERSITY_NAME', 'Binod Bihari Mahto Koyalanchal University (BBMKU)', 'Official University Name', 'Branding'),
            ('UNIVERSITY_CODE', 'BBMKU', 'University Abbreviation Code', 'Branding'),
            ('UNIVERSITY_LOCATION', 'Dhanbad, Jharkhand, India', 'Location of University Headquarters', 'Branding')
        ]
        for key, val, desc, cat in settings_data:
            SystemSetting.set_value(key, val, desc, cat)

        print("Seeding realistic university files and movement histories...")
        now = datetime.now(timezone.utc)
        today = date.today()

        # Helper to create file with movements and notings
        files_to_seed = [
            {
                'number': 'BBMKU/ESTB/2026/0001',
                'subject': 'Sanction of Leave and LTC for Teaching Faculty for Academic Year 2026-27',
                'desc': 'Consolidated applications of University Department Professors seeking permission for LTC block year 2026.',
                'cat': 'Establishment',
                'prio': 'Normal',
                'conf': 'General',
                'status': 'Under Process',
                'init_user': 'da_admin',
                'init_dept': 'ESTB',
                'curr_user': 'so_establishment',
                'curr_dept': 'ESTB',
                'created_delta': 4,
                'assigned_delta': 2,
                'due_date': today + timedelta(days=10),
                'last_action': 'Received by Section Officer (Establishment)',
                'next_action': 'Verification of service book entries and forwarding to Registrar',
                'notes': [
                    ('da_admin', 'Put up for consideration. Applications of 14 faculty members verified against admissible leave credits under Statute Section 14.', 1),
                    ('so_establishment', 'Scrutiny in progress. Checking eligibility of 3 faculty members who joined in the last 2 years.', 2)
                ]
            },
            {
                'number': 'BBMKU/FIN/2026/0002',
                'subject': 'Annual Budget Allocation and Grants Utilization for Departmental Research Labs',
                'desc': 'Distribution of State Higher Education Plan grants among Science and Technology departments for laboratory consumables.',
                'cat': 'Financial',
                'prio': 'Urgent',
                'conf': 'Confidential',
                'status': 'Forwarded',
                'init_user': 'so_accounts',
                'init_dept': 'FIN',
                'curr_user': 'fo_bbmku',
                'curr_dept': 'FIN',
                'created_delta': 5,
                'assigned_delta': 1,
                'due_date': today + timedelta(days=5),
                'last_action': 'Forwarded to Finance Officer, BBMKU',
                'next_action': 'Recommendation on fund allocation formula',
                'notes': [
                    ('so_accounts', 'Detailed budget draft prepared. Total requisition Rs. 2.45 Crores against allocated budget head 2202.', 1)
                ]
            },
            {
                'number': 'BBMKU/EXAM/2026/0003',
                'subject': 'Printing of Security Blank Marksheets and Digital Degree Certificates for 5th Convocation',
                'desc': 'Confidential tender specification for tamper-proof holographic marksheets and QR-coded degree certificates.',
                'cat': 'Examination',
                'prio': 'Immediate',
                'conf': 'Confidential',
                'status': 'Pending Approval',
                'init_user': 'coe_bbmku',
                'init_dept': 'EXAM',
                'curr_user': 'vc_bbmku',
                'curr_dept': 'VCO',
                'created_delta': 6,
                'assigned_delta': 1,
                'due_date': today + timedelta(days=2),
                'last_action': 'Submitted for Approval to Vice-Chancellor',
                'next_action': 'Hon\'ble VC Sir sanction and approval',
                'notes': [
                    ('coe_bbmku', 'All security features (micro-line printing, rainbow tint, latent image) approved by Examination Committee. Submitted for sanction of Hon\'ble VC.', 1)
                ]
            },
            {
                'number': 'BBMKU/ACAD/2026/0004',
                'subject': 'Proposal for Introduction of PG Diploma in Mining Environment and Sustainable Energy',
                'desc': 'Course structure, credit framework, and industry linkage with BCCL and CMPDI.',
                'cat': 'Academic',
                'prio': 'Normal',
                'conf': 'General',
                'status': 'Under Process',
                'init_user': 'registrar',
                'init_dept': 'ACAD',
                'curr_user': 'registrar',
                'curr_dept': 'REG',
                'created_delta': 10,
                'assigned_delta': 4,
                'due_date': today + timedelta(days=12),
                'last_action': 'Review and Initial Noting',
                'next_action': 'Constitution of Board of Studies Expert Committee',
                'notes': [
                    ('registrar', 'Proposal initiated following industry-academia advisory council recommendations in Dhanbad coal belt.', 1)
                ]
            },
            {
                'number': 'BBMKU/ADM/2026/0005',
                'subject': 'Centralized UG/PG Admissions Verification through Chancellor Portal',
                'desc': 'Verification report for university admissions under Jharkhand Chancellor Portal.',
                'cat': 'Student Affairs',
                'prio': 'Urgent',
                'conf': 'General',
                'status': 'Approved',
                'init_user': 'dsw_bbmku',
                'init_dept': 'ADM',
                'curr_user': 'dsw_bbmku',
                'curr_dept': 'ADM',
                'created_delta': 12,
                'assigned_delta': 2,
                'due_date': today - timedelta(days=2),
                'last_action': 'Approved by Vice-Chancellor, BBMKU',
                'next_action': 'Transmission of signed admissions lists',
                'notes': [
                    ('dsw_bbmku', 'All college verification certificates cross-checked. Eligible student database finalized.', 1),
                    ('vc_bbmku', 'Approved. Prompt transmission directed.', 2)
                ]
            },
            {
                'number': 'BBMKU/RUSA/2026/0006',
                'subject': 'RUSA Infrastructure Grant Allocation and High-Speed Networking Procurement',
                'desc': 'RUSA project procurement file for database hardware, networking rack, and lab equipment.',
                'cat': 'Purchase/Store',
                'prio': 'Immediate',
                'conf': 'General',
                'status': 'Under Process',
                'init_user': 'admin',
                'init_dept': 'RUSA',
                'curr_user': 'fo_bbmku',
                'curr_dept': 'FIN',
                'created_delta': 22,
                'assigned_delta': 18, # > 15 days, intentionally overdue for delay testing
                'due_date': today - timedelta(days=5), # breached due date
                'last_action': 'Forwarded to Finance Officer for Financial Concurrence',
                'next_action': 'Financial Concurrence and Issuance of GeM Bid',
                'notes': [
                    ('admin', 'Technical evaluation completed. Three qualifying bidders identified on GeM. Awaiting financial concurrence.', 1)
                ]
            },
            {
                'number': 'BBMKU/AFF/2026/0007',
                'subject': 'Inspection Compliance for College Affiliation in Dhanbad and Bokaro Districts',
                'desc': 'Draft inspection report regarding affiliation compliance and land title norms for affiliated colleges.',
                'cat': 'Academic',
                'prio': 'Urgent',
                'conf': 'Confidential',
                'status': 'Returned for Correction',
                'init_user': 'da_admin',
                'init_dept': 'AFF',
                'curr_user': 'da_admin',
                'curr_dept': 'ESTB',
                'created_delta': 8,
                'assigned_delta': 2,
                'due_date': today + timedelta(days=3),
                'last_action': 'Returned for Correction by Registrar, BBMKU',
                'next_action': 'Correction of annexures and resubmission',
                'notes': [
                    ('da_admin', 'Draft counter affidavit prepared based on file notes from Affiliation Branch.', 1)
                ]
            },
            {
                'number': 'BBMKU/ESTB/2026/0008',
                'subject': 'Confirmation of Service for Non-Teaching Staff Appointed in Phase-II',
                'desc': 'Completion of 2-year satisfactory probation period and police verification reports.',
                'cat': 'Establishment',
                'prio': 'Normal',
                'conf': 'General',
                'status': 'Closed',
                'init_user': 'so_establishment',
                'init_dept': 'ESTB',
                'curr_user': 'registrar',
                'curr_dept': 'REG',
                'created_delta': 30,
                'assigned_delta': 5,
                'due_date': today - timedelta(days=10),
                'last_action': 'Closed by Registrar, BBMKU',
                'next_action': 'Ready for Record Archival',
                'notes': [
                    ('so_establishment', 'Police verification and satisfactory work report received for all 18 assistants.', 1),
                    ('registrar', 'Executive order issued confirming service. File objectives fulfilled. Closed.', 2)
                ]
            },
            {
                'number': 'BBMKU/REG/2026/0009',
                'subject': 'Statutory Notification for Affiliation of New Degree Colleges in Dhanbad and Bokaro Districts',
                'desc': 'Gazette publication and university record copy of approved college affiliations for academic session 2025-26.',
                'cat': 'Academic',
                'prio': 'Normal',
                'conf': 'General',
                'status': 'Archived',
                'init_user': 'registrar',
                'init_dept': 'REG',
                'curr_user': 'admin',
                'curr_dept': 'REG',
                'created_delta': 45,
                'assigned_delta': 10,
                'due_date': today - timedelta(days=20),
                'last_action': 'Archived at Central Record Room Rack A-12, Shelf 3',
                'next_action': 'Permanent University Record Archive',
                'notes': [
                    ('registrar', 'Gazette copies received and verified. File closed and marked for permanent archival preservation.', 1)
                ]
            }
        ]

        for fd in files_to_seed:
            created_dt = now - timedelta(days=fd['created_delta'])
            assigned_dt = now - timedelta(days=fd['assigned_delta'])
            init_user = user_objs[fd['init_user']]
            init_dept = dept_objs[fd['init_dept']]
            curr_user = user_objs[fd['curr_user']]
            curr_dept = dept_objs[fd['curr_dept']]

            file_rec = FileRecord(
                file_number=fd['number'],
                subject=fd['subject'],
                description=fd['desc'],
                category=fd['cat'],
                priority=fd['prio'],
                confidentiality=fd['conf'],
                status=fd['status'],
                initiating_officer_id=init_user.id,
                initiating_department_id=init_dept.id,
                current_officer_id=curr_user.id,
                current_department_id=curr_dept.id,
                created_at=created_dt,
                due_date=fd['due_date'],
                assigned_at=assigned_dt,
                received_at=assigned_dt if fd['status'] != 'Awaiting Receipt' else None,
                last_action=fd['last_action'],
                last_action_at=assigned_dt,
                next_expected_action=fd['next_action']
            )

            if fd['status'] == 'Closed':
                file_rec.closure_date = now - timedelta(days=3)
                file_rec.closure_remarks = 'Executive order issued confirming service. File closed.'
                file_rec.closed_by_id = user_objs['registrar'].id
            elif fd['status'] == 'Archived':
                file_rec.closure_date = now - timedelta(days=15)
                file_rec.archived_date = now - timedelta(days=5)
                file_rec.archived_location = 'Central Record Room Rack A-12, Shelf 3'
                file_rec.archived_by_id = user_objs['admin'].id

            db.session.add(file_rec)
            db.session.flush()

            # Add movements
            mov1 = FileMovement(
                file_id=file_rec.id,
                from_user_id=init_user.id,
                to_user_id=curr_user.id,
                from_department_id=init_dept.id,
                to_department_id=curr_dept.id,
                movement_type='Forward' if init_user.id != curr_user.id else 'Submit',
                action_taken=fd['last_action'],
                remarks=f"Transferred for administrative processing: {fd['subject']}",
                dispatch_date=created_dt,
                dispatch_mode='Digital Workflow',
                is_received=True,
                received_date=assigned_dt
            )
            db.session.add(mov1)

            # Add notes
            for author_uname, content, num in fd['notes']:
                author = user_objs[author_uname]
                note = FileNote(
                    file_id=file_rec.id,
                    note_number=num,
                    content=content,
                    note_type='Formal Minute' if num > 1 else 'Internal Note',
                    author_id=author.id,
                    author_designation=author.designation,
                    department_id=author.department_id,
                    created_at=created_dt + timedelta(days=num - 1)
                )
                db.session.add(note)

            # Add decisions for Approved, Rejected, Returned, Closed, Archived
            if fd['status'] == 'Approved':
                dec = FileDecision(
                    file_id=file_rec.id,
                    officer_id=user_objs['vc_bbmku'].id,
                    decision_type='Approved',
                    remarks='Sanctioned as proposed. Ensure timely compliance.',
                    conditions='Subject to availability of State Government budget sanction.',
                    decided_at=assigned_dt
                )
                db.session.add(dec)
            elif fd['status'] == 'Returned for Correction':
                dec = FileDecision(
                    file_id=file_rec.id,
                    officer_id=user_objs['registrar'].id,
                    decision_type='Returned for Correction',
                    remarks='Annexures 4 and 6 are missing certified copies of land mutation.',
                    reason='Incomplete statutory documentation.',
                    correction_instructions='Attach certified mutation certificate and re-route through Legal Cell within 48 hours.',
                    decided_at=assigned_dt
                )
                db.session.add(dec)
            elif fd['status'] == 'Closed':
                dec = FileDecision(
                    file_id=file_rec.id,
                    officer_id=user_objs['registrar'].id,
                    decision_type='Closed',
                    remarks='All confirmation orders dispatched. File closed.',
                    decided_at=now - timedelta(days=3)
                )
                db.session.add(dec)
            elif fd['status'] == 'Archived':
                dec = FileDecision(
                    file_id=file_rec.id,
                    officer_id=user_objs['admin'].id,
                    decision_type='Archived',
                    remarks='Permanent retention at Central Record Room Rack A-12, Shelf 3',
                    decided_at=now - timedelta(days=5)
                )
                db.session.add(dec)

        db.session.commit()
        print("Database seeded successfully with BBMKU University sample records!")


if __name__ == '__main__':
    import sys
    is_reset = '--reset' in sys.argv
    seed_database(reset=is_reset)
