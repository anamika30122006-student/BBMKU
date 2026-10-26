from typing import Optional
from flask import request
from flask_login import current_user
from app.extensions import db
from app.models.audit import AuditLog


def log_audit_event(
    action: str,
    file_id: Optional[int] = None,
    file_number: Optional[str] = None,
    previous_state: Optional[str] = None,
    new_state: Optional[str] = None,
    remarks: Optional[str] = None,
    user=None
):
    """
    Records an immutable audit event for university administrative integrity.
    """
    try:
        actor = user or (current_user if current_user.is_authenticated else None)
        user_id = actor.id if actor else None
        user_name = actor.full_name if actor else 'System Process'
        user_role = actor.role.name if actor and actor.role else 'SYSTEM'

        ip_address = None
        user_agent = None
        if request:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')[:250]

        log_entry = AuditLog(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            action=action,
            file_id=file_id,
            file_number=file_number,
            previous_state=previous_state,
            new_state=new_state,
            remarks=remarks,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        # Audit logging failure must not break main execution, but roll back subtransaction
        db.session.rollback()
