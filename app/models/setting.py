from datetime import datetime, timezone
from app.extensions import db


class SystemSetting(db.Model):
    """Dynamic university settings (SLA thresholds, numbering prefixes, retention)."""
    __tablename__ = 'system_settings'

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(64), default='General')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_value(cls, key: str, default=None):
        setting = db.session.get(cls, key)
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key: str, value: str, description=None, category='General'):
        setting = db.session.get(cls, key)
        if not setting:
            setting = cls(key=key, value=str(value), description=description, category=category)
            db.session.add(setting)
        else:
            setting.value = str(value)
            if description:
                setting.description = description
        db.session.commit()
        return setting

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<SystemSetting {self.key}={self.value}>'
