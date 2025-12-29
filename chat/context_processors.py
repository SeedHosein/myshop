from .models import ChatSession

def chat_session_context(request):
    chat_session_id = None
    if request.user.is_authenticated and not request.user.is_staff:
        # Try to find an active session for the user
        session = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-updated_at').first()
        if not session:
            # If no active session, create a new one
            session = ChatSession.objects.create(user=request.user)
        chat_session_id = str(session.id)
    # Staff users do not get an automatic session ID in this context,
    # they manage chats via the support dashboard.

    return {
        'CHAT_SESSION_ID': chat_session_id
    }