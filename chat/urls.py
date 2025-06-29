from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Customer-facing chat room
    path('', views.ChatRoomView.as_view(), name='start_chat'), # Start a new chat or find existing
    path('<uuid:session_id>/', views.ChatRoomView.as_view(), name='chat_room_with_id'),

    # Support staff dashboard and joining specific chats
    path('support/', views.SupportChatDashboardView.as_view(), name='support_dashboard'),
    path('support/session/<uuid:session_id>/', views.SupportJoinChatView.as_view(), name='support_join_chat'),
] 