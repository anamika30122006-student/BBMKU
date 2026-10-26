from datetime import datetime, timezone
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

# Association table between roles and permissions
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class Permission(db.Model):
    """Granular permissions for university administrative actions."""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(64), default='General')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Permission {self.code}>'


class Role(db.Model):
    """University administrative roles."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    is_system_role = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    permissions = db.relationship(
        'Permission',
        secondary=role_permissions,
        backref=db.backref('roles', lazy='dynamic'),
        lazy='joined'
    )
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def has_permission(self, perm_code: str) -> bool:
        return any(p.code == perm_code for p in self.permissions)

    def add_permission(self, perm: Permission):
        if perm not in self.permissions:
            self.permissions.append(perm)

    def remove_permission(self, perm: Permission):
        if perm in self.permissions:
            self.permissions.remove(perm)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """University officer and administrative user account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    designation = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    role = db.relationship('Role', back_populates='users', lazy='joined')
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='users', lazy='joined')
    section = db.relationship('Section', foreign_keys=[section_id], lazy='joined')

    assigned_files = db.relationship('FileRecord', foreign_keys='FileRecord.current_officer_id', back_populates='current_officer', lazy='dynamic')
    initiated_files = db.relationship('FileRecord', foreign_keys='FileRecord.initiating_officer_id', back_populates='initiating_officer', lazy='dynamic')
    notes = db.relationship('FileNote', back_populates='author', lazy='dynamic')
    decisions = db.relationship('FileDecision', back_populates='officer', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm_code: str) -> bool:
        if not self.is_active or not self.role:
            return False
        # System Admin has all permissions implicitly
        if self.role.name == 'SYSTEM_ADMIN':
            return True
        return self.role.has_permission(perm_code)

    @property
    def is_ec_sir(self) -> bool:
        return self.role.name == 'EC_VIEWER'

    @property
    def is_admin(self) -> bool:
        return self.role.name == 'SYSTEM_ADMIN'

    @property
    def can_approve(self) -> bool:
        return self.has_permission('approve_file')

    @property
    def can_create(self) -> bool:
        return self.has_permission('create_file')

    @property
    def can_forward(self) -> bool:
        return self.has_permission('forward_file')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<User {self.username} - {self.designation}>'


class AnonymousUser(AnonymousUserMixin):
    """Anonymous user with default no-op permissions for safe template evaluation."""
    def has_permission(self, perm_code: str) -> bool:
        return False

    @property
    def is_admin(self) -> bool:
        return False

    @property
    def is_ec_sir(self) -> bool:
        return False
