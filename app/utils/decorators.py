from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user


def permission_required(permission_code: str):
    """Decorator to require a specific permission code for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_permission(permission_code):
                flash('You do not have administrative permission to perform this action.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*roles):
    """Decorator to require one of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role.name not in roles and current_user.role.name != 'SYSTEM_ADMIN':
                flash('Access denied: your role does not have authorization for this section.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator requiring System Administrator role."""
    return role_required('SYSTEM_ADMIN')(f)
