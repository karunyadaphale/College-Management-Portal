"""
Context processor to make logged in user session information available
to all Django templates automatically.
"""

def mongo_user_context(request):
    """
    Exposes MongoDB session user info to templates:
    - current_user: dict of session details (or None)
    - user_role: 'admin', 'faculty', 'student', or None
    - is_authenticated: Boolean
    """
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    name = request.session.get('name')
    email = request.session.get('email')

    if user_id:
        return {
            'current_user': {
                'user_id': user_id,
                'role': role,
                'name': name,
                'email': email,
            },
            'user_role': role,
            'is_authenticated': True,
        }
    return {
        'current_user': None,
        'user_role': None,
        'is_authenticated': False,
    }
