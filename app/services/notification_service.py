from typing import Optional
from app.extensions import db
from app.models.notification import Notification


def send_notification(
    user_id: int,
    title: str,
    message: str,
    file_id: Optional[int] = None,
    notification_type: str = 'Assignment'
):
    """
    Creates an in-application notification for a university officer.
    """
    try:
        notification = Notification(
            user_id=user_id,
            file_id=file_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        db.session.add(notification)
        db.session.commit()
    except Exception:
        db.session.rollback()
