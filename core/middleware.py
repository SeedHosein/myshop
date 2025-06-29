from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
import time
from .models import SiteVisit

class PageViewCounterMiddleware(MiddlewareMixin):
    def process_request(self, request):
        SiteVisit.increment_visit_count()

class ActiveUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        last_seen = cache.get(f'last-seen-{request.user.id}')
        if not last_seen:
            cache.set(f'last-seen-{request.user.id}', time.time())

class OnlineUsersMiddleware(MiddlewareMixin):
    def process_request(self, request):
        current_user = request.user
        now = time.time()
        
        # Get all online users from cache
        online_users = cache.get('online-users', {})

        if current_user.is_authenticated:
            # Update last seen time for authenticated user
            online_users[current_user.id] = now
        else:
            # For anonymous users, use session key
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            online_users[session_key] = now

        # Remove users who were last seen more than 5 minutes ago
        timeout = 300  # 5 minutes
        online_users = {u: t for u, t in online_users.items() if now - t < timeout}
        
        cache.set('online-users', online_users, timeout) 