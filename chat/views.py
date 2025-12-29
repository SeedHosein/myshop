from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.conf import settings

from .models import ChatSession, ChatMessage
from django.http import Http404
import uuid

# class ChatRoomView(LoginRequiredMixin, View):
#     def get(self, request, session_id=None):
#         chat_session = None
#         if session_id:
#             try:
#                 # User can only access their own sessions or if they are staff
#                 chat_session = ChatSession.objects.get(id=session_id)
#                 if not (chat_session.user == request.user or request.user.is_staff):
#                     raise Http404("جلسه گفتگو یافت نشد یا دسترسی ممنوع است.")
#             except (ChatSession.DoesNotExist, ValueError):
#                 raise Http404("شناسه جلسه گفتگو نامعتبر است.")
#         else:
#             # For a regular user, try to find an existing active session or create a new one
#             if not request.user.is_staff:
#                 chat_session = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-created_at').first()
            
#             if not chat_session:
#                 # If no session_id is provided and no active session exists for the user,
#                 # or if user is staff and wants to start a new chat (less common scenario here, usually they join)
#                 # For a customer, create a new one.
#                 if not request.user.is_staff:
#                     chat_session = ChatSession.objects.create(user=request.user)
#                     return redirect(reverse('chat:chat_room_with_id', kwargs={'session_id': str(chat_session.id)}))
#                 else:
#                     # Staff usually join existing sessions via dashboard, but allow direct access if ID provided
#                     # Or we can redirect them to dashboard if no ID
#                     return redirect(reverse('chat:support_dashboard')) 

#         if not chat_session:
#              raise Http404("امکان شروع یا یافتن جلسه گفتگو وجود ندارد.")
#         context = {
#             'chat_session_id': str(chat_session.id),
#             'chat_session': chat_session,
#             'current_user_email': request.user.email
#         }
#         context['SHOP_NAME'] = settings.SHOP_NAME
#         return render(request, 'chat/chat_room.html', context)

class SupportStaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class SupportChatDashboardView(LoginRequiredMixin, SupportStaffRequiredMixin, View):
    def get(self, request):
        # List active sessions, or sessions needing attention
        if self.request.user.is_superuser:
            active_sessions = ChatSession.objects.all().order_by('-updated_at')
        else:
            active_sessions = ChatSession.objects.filter(Q(support_agent=request.user) | Q(support_agent=None) & Q(is_active=True)).order_by('-updated_at')

        # You might want more complex filtering, e.g., sessions with unread messages by agent
        context = {
            'active_sessions': active_sessions
        }
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, 'chat/support_chat_dashboard.html', context)

# View for support staff to join a specific chat
class SupportJoinChatView(LoginRequiredMixin, SupportStaffRequiredMixin, View):
    def get(self, request, session_id):
        try:
            chat_session = ChatSession.objects.get(id=session_id, is_active=True)
        except (ChatSession.DoesNotExist, ValueError):
            raise Http404("شناسه جلسه گفتگو نامعتبر است یا غیر فعال شده است.")
        
        if not request.user.get_short_name_staff:
            messages.error(request, "ابتدا باید نام و نام خانوادگی خود را در پروفایلتان وارد کنید.")
            return redirect("chat:support_dashboard")

        # Agent is joining, assign them if no one is there or they are rejoining
        if not chat_session.support_agent or chat_session.support_agent != request.user:
            chat_session.support_agent = request.user
            chat_session.save() 
        context = {
            'chat_session_id': str(chat_session.id),
            'chat_session': chat_session,
            'is_support_staff': True, # Differentiate in template if needed
            'current_user_email': request.user.email
        }
        context['SHOP_NAME'] = settings.SHOP_NAME
        return render(request, 'chat/chat_room.html', context)
