from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Support staff dashboard and joining specific chats
    path('support/', views.SupportChatDashboardView.as_view(), name='support_dashboard'),
    path('support/session/<uuid:session_id>/', views.SupportJoinChatView.as_view(), name='support_join_chat'),
]
