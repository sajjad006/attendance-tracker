from .signals import set_current_user, clear_current_user


class AuditLogMiddleware:
    """
    Middleware to capture request context for audit logging.
    Sets the current user, IP address, and user agent for audit logs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get user if authenticated
        user = request.user if hasattr(request, "user") and request.user.is_authenticated else None
        
        # Get IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")
        
        # Get user agent
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        
        # Set context for audit logging
        set_current_user(user, ip_address, user_agent)
        
        try:
            response = self.get_response(request)
        finally:
            # Clear context after request
            clear_current_user()
        
        return response
