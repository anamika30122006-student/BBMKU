import pytest
from datetime import datetime, timezone, date, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User, Role, Permission
from app.models.department import Department, Section
from app.models.file import FileRecord
from app.models.setting import SystemSetting


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed basic roles & permissions
        perms = [
            Permission(code='view_all_files', name='View All Files'),
            Permission(code='create_file', name='Create File'),
            Permission(code='forward_file', name='Forward File'),
            Permission(code='receive_file', name='Receive File'),
            Permission(code='return_file', name='Return File'),
            Permission(code='add_note', name='Add Note'),
            Permission(code='upload_document', name='Upload Document'),
            Permission(code='approve_file', name='Approve File'),
            Permission(code='reject_file', name='Reject File'),
            Permission(code='close_file', name='Close File'),
            Permission(code='archive_file', name='Archive File'),
            Permission(code='view_reports', name='View Reports'),
            Permission(code='export_reports', name='Export Reports'),
            Permission(code='view_audit_logs', name='View Audit Logs'),
            Permission(code='manage_users', name='Manage Users')
        ]
        db.session.add_all(perms)
        db.session.commit()

        # Roles
        admin_role = Role(name='SYSTEM_ADMIN', display_name='System Admin')
        ec_role = Role(name='EC_VIEWER', display_name='EC Sir')
        vc_role = Role(name='APPROVING_AUTHORITY', display_name='Vice-Chancellor')
        da_role = Role(name='DEALING_ASSISTANT', display_name='Dealing Assistant')
        so_role = Role(name='SECTION_OFFICER', display_name='Section Officer')
        db.session.add_all([admin_role, ec_role, vc_role, da_role, so_role])

        for p in perms:
            admin_role.add_permission(p)

        ec_role.add_permission(Permission.query.filter_by(code='view_all_files').first())
        ec_role.add_permission(Permission.query.filter_by(code='view_reports').first())
        ec_role.add_permission(Permission.query.filter_by(code='view_audit_logs').first())

        for code in ['view_all_files', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document', 'approve_file', 'reject_file', 'close_file', 'archive_file']:
            vc_role.add_permission(Permission.query.filter_by(code=code).first())

        for code in ['create_file', 'forward_file', 'receive_file', 'add_note', 'upload_document']:
            da_role.add_permission(Permission.query.filter_by(code=code).first())

        for code in ['create_file', 'forward_file', 'receive_file', 'return_file', 'add_note', 'upload_document']:
            so_role.add_permission(Permission.query.filter_by(code=code).first())

        db.session.add_all([admin_role, ec_role, vc_role, da_role, so_role])
        db.session.commit()

        # Department
        dept = Department(name='Establishment Section', code='ESTB')
        db.session.add(dept)
        db.session.commit()

        # Users
        u_admin = User(username='admin', email='admin@bbmku.ac.in', full_name='System Administrator', designation='Admin', role_id=admin_role.id, department_id=dept.id)
        u_admin.set_password('Admin@123')

        u_ec = User(username='ec_sir', email='ec@bbmku.ac.in', full_name='Hon\'ble EC Sir', designation='EC Member', role_id=ec_role.id)
        u_ec.set_password('Password@123')

        u_vc = User(username='vc_bbmku', email='vc@bbmku.ac.in', full_name='Vice-Chancellor', designation='VC', role_id=vc_role.id)
        u_vc.set_password('Password@123')

        u_so = User(username='so_estb', email='so@bbmku.ac.in', full_name='Section Officer', designation='SO Estb', role_id=so_role.id, department_id=dept.id)
        u_so.set_password('Password@123')

        u_da = User(username='da_estb', email='da@bbmku.ac.in', full_name='Dealing Assistant', designation='DA Estb', role_id=da_role.id, department_id=dept.id)
        u_da.set_password('Password@123')

        db.session.add_all([u_admin, u_ec, u_vc, u_so, u_da])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login_helper(client, username, password='Password@123'):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)
