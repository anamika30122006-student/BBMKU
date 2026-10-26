import pytest
from app.extensions import db
from app.models.file import FileRecord, FileMovement, FileDecision
from app.models.user import User
from app.models.department import Department
from app.services.file_service import (
    create_file_record,
    forward_file,
    confirm_receipt,
    approve_file,
    reject_file,
    return_file_for_correction
)


def test_file_creation_and_numbering(app):
    with app.app_context():
        da = User.query.filter_by(username='da_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()

        f1 = create_file_record(
            subject='Proposal for Faculty Medical Reimbursment',
            description='Testing medical bills verification',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept,
            initial_remarks='Initial noting by Dealing Assistant'
        )

        assert f1.id is not None
        assert f1.file_number.startswith('BBMKU/ESTB/')
        assert f1.status == 'Draft'
        assert f1.current_officer_id == da.id
        assert len(f1.notes) == 1
        assert f1.notes[0].note_number == 1


def test_file_forwarding_and_receipt(app):
    with app.app_context():
        da = User.query.filter_by(username='da_estb').first()
        so = User.query.filter_by(username='so_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()

        f = create_file_record(
            subject='Leave Sanction File',
            description='Test description',
            category='Establishment',
            priority='Urgent',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )

        # Forward file from DA to SO
        mov = forward_file(
            file_record=f,
            from_user=da,
            to_user=so,
            remarks='Put up for verification and recommendation',
            action_type='For Verification & Scrutiny'
        )

        assert f.status == 'Awaiting Receipt'
        assert f.current_officer_id == so.id
        assert mov.is_received is False

        # Confirm receipt by SO
        confirm_receipt(f, so, remarks='Received and taken up for checking')

        assert f.status == 'Under Process'
        assert f.received_at is not None
        assert mov.is_received is True


def test_file_return_for_correction(app):
    with app.app_context():
        da = User.query.filter_by(username='da_estb').first()
        so = User.query.filter_by(username='so_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()

        f = create_file_record(
            subject='Promotion Scrutiny File',
            description='Test',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )

        forward_file(f, da, so, remarks='Check promotion eligibility')
        confirm_receipt(f, so)

        # SO returns file to DA for correction
        dec = return_file_for_correction(
            file_record=f,
            returning_user=so,
            return_to_user=da,
            reason='Service book entry missing',
            correction_instructions='Attach verified copy of service register page 4'
        )

        assert f.status == 'Returned for Correction'
        assert f.current_officer_id == da.id
        assert dec.decision_type == 'Returned for Correction'
        assert dec.reason == 'Service book entry missing'


def test_approval_and_rejection_decisions(app):
    with app.app_context():
        vc = User.query.filter_by(username='vc_bbmku').first()
        da = User.query.filter_by(username='da_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()

        f_appr = create_file_record(
            subject='Approval Test File',
            description='Test',
            category='Establishment',
            priority='Urgent',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )

        dec_appr = approve_file(f_appr, vc, remarks='Formally approved and sanctioned.')
        assert f_appr.status == 'Approved'
        assert dec_appr.decision_type == 'Approved'

        f_rej = create_file_record(
            subject='Rejection Test File',
            description='Test',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )

        dec_rej = reject_file(f_rej, vc, reason='In violation of UGC norms', remarks='Rejected as per Ordinance Section 9')
        assert f_rej.status == 'Rejected'
        assert dec_rej.decision_type == 'Rejected'
        assert dec_rej.reason == 'In violation of UGC norms'


def test_delete_file_record(app, client):
    with app.app_context():
        da = User.query.filter_by(username='da_estb').first()
        dept = Department.query.filter_by(code='ESTB').first()

        f = create_file_record(
            subject='File To Be Deleted',
            description='Test Delete',
            category='Establishment',
            priority='Normal',
            confidentiality='General',
            initiating_officer=da,
            initiating_department=dept
        )
        file_id = f.id

    # Log in as admin to delete file
    client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    res = client.post(f'/files/{file_id}/delete', follow_redirects=True)
    assert res.status_code == 200
    assert b'successfully deleted' in res.data

    with app.app_context():
        deleted = db.session.get(FileRecord, file_id)
        assert deleted is None

