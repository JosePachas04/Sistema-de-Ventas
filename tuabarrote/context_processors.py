from flask import current_app
from .services.auth_service import is_logged_in, is_admin, is_customer, get_user_role

@current_app.context_processor
def inject_user_status():
    return dict(
        is_logged_in=is_logged_in,
        is_admin=is_admin,
        is_customer=is_customer,
        user_role=get_user_role()
    )
