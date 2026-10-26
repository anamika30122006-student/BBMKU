import pytest
from datetime import datetime, timezone, timedelta, date
from app.extensions import db
from app.models.file import FileRecord
from app.models.user import User
from app.models.department import Department
from app.services.file_service import create_file_record
from app.services.metrics_service import get_dashboard_metrics


def test_delay_and_overdue_calculation(app):
    with app.app_context():
        da = User.query.filter_by(username='da_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()
        now = datetime.now(timezone.utc)
        today = date.today()

        # 1. Fresh file (On Track)
        f_fresh = create_file_record(
            subject='Fresh File',
            description='Test',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )
        assert f_fresh.pending_days == 0
        assert f_fresh.delay_status == 'On Track'
        assert f_fresh.is_overdue is False

        # 2. Delayed file (4 days old)
        f_delayed = create_file_record(
            subject='Delayed File',
            description='Test',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )
        f_delayed.assigned_at = now - timedelta(days=4)
        f_delayed.received_at = now - timedelta(days=4)
        db.session.commit()
        assert f_delayed.pending_days == 4
        assert f_delayed.delay_status == 'Delayed'

        # 3. Critical delayed file (8 days old)
        f_critical = create_file_record(
            subject='Critical Delayed File',
            description='Test',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )
        f_critical.assigned_at = now - timedelta(days=8)
        f_critical.received_at = now - timedelta(days=8)
        db.session.commit()
        assert f_critical.pending_days == 8
        assert f_critical.delay_status == 'Critical Delay'

        # 4. Overdue file (past due date)
        f_overdue = create_file_record(
            subject='Overdue File',
            description='Test',
            category='Establishment',
            priority='Immediate',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept,
            due_date=today - timedelta(days=2)
        )
        assert f_overdue.is_overdue is True
        assert f_overdue.delay_status == 'Overdue'


def test_metrics_calculation(app):
    with app.app_context():
        metrics = get_dashboard_metrics()
        assert 'total_files' in metrics
        assert 'pending_files' in metrics
        assert 'approved_files' in metrics
        assert 'overdue_files' in metrics
        assert metrics['total_files'] >= 0


def test_csv_export(client):
    # Log in as admin
    client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    res = client.get('/reports/export/csv?type=total_files')
    assert res.status_code == 200
    assert 'text/csv' in res.content_type
    assert b'File Number' in res.data
    assert b'Subject' in res.data


def test_mobile_screens_render(client):
    client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    res_reports = client.get('/reports')
    assert res_reports.status_code == 200
    assert b'Officer Desk Workload' in res_reports.data
    assert b'mobile-workload-list' in res_reports.data

    res_profile = client.get('/auth/profile')
    assert res_profile.status_code == 200
    assert b'app-profile-hero' in res_profile.data
    assert b'app-profile-group' in res_profile.data

