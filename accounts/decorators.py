"""
Custom decorators for MongoDB session-based authentication and role authorization.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_required_mongo(view_func):
    """
    Decorator to ensure user is logged in via session.
    Redirects to login page if session is missing.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.warning(request, "Please log in to access this page.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(allowed_roles):
    """
    Decorator to restrict access to specific roles.
    Example usage: @role_required(['admin']) or @role_required(['admin', 'faculty'])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.session.get('user_id'):
                messages.warning(request, "Please log in to continue.")
                return redirect('accounts:login')

            user_role = request.session.get('role')
            if user_role not in allowed_roles:
                messages.error(request, "Access Denied: You do not have permission to view this page.")
                # Redirect user to their respective dashboard
                if user_role == 'admin':
                    return redirect('accounts:admin_dashboard')
                elif user_role == 'faculty':
                    return redirect('accounts:faculty_dashboard')
                elif user_role == 'student':
                    return redirect('accounts:student_dashboard')
                else:
                    return redirect('accounts:login')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
