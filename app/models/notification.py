from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    """In-application alerts and notifications for university officers."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='SET NULL'), nullable=True, index=True)
    
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Notification types:
    # Assignment, Movement, Receipt, Approval, Rejection, Return, Overdue, General
    notification_type = db.Column(db.String(40), default='Assignment', index=True)
    
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = db.relationship('User', back_populates='notifications')
    file = db.relationship('FileRecord')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Notification {self.notification_type}: {self.title}>'
