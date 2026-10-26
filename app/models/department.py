from datetime import datetime, timezone
from app.extensions import db


class Department(db.Model):
    """BBMKU University Departments and Administrative Branches."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    sections = db.relationship('Section', back_populates='department', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', foreign_keys='User.department_id', back_populates='department', lazy='dynamic')
    
    files_initiated = db.relationship('FileRecord', foreign_keys='FileRecord.initiating_department_id', back_populates='initiating_department', lazy='dynamic')
    current_files = db.relationship('FileRecord', foreign_keys='FileRecord.current_department_id', back_populates='current_department', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Department {self.code} - {self.name}>'


class Section(db.Model):
    """Sub-units, cells, or sections within a Department."""
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    department = db.relationship('Department', back_populates='sections', lazy='joined')
    users = db.relationship('User', foreign_keys='User.section_id', back_populates='section', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Section {self.code} - {self.name}>'
