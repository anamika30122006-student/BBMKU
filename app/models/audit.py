from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Immutable audit trail for file creation, movements, notes, approvals, closures, and security events."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    user_name = db.Column(db.String(120), nullable=False)
    user_role = db.Column(db.String(64), nullable=True)

    action = db.Column(db.String(100), nullable=False, index=True) # File Created, Forwarded, Received, Approved, Rejected, etc.
    file_id = db.Column(db.Integer, nullable=True, index=True)
    file_number = db.Column(db.String(64), nullable=True, index=True)

    previous_state = db.Column(db.String(64), nullable=True)
    new_state = db.Column(db.String(64), nullable=True)

    remarks = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationship
    user = db.relationship('User', lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<AuditLog {self.timestamp} - {self.action} on {self.file_number} by {self.user_name}>'
