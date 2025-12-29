from django.db import models
from django.conf import settings
# from django.utils.translation import gettext_lazy as _ # No longer needed
import uuid

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # Keep chat history even if user is deleted
        null=True, 
        blank=True, 
        verbose_name="کاربر",
        related_name="chat_sessions"
    )
    support_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پشتیبان",
        related_name="support_chat_sessions",
        limit_choices_to={'is_staff': True} # Only staff can be support agents
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    is_active = models.BooleanField(default=True, verbose_name="فعال است")
    # guest_email for unauthenticated users, if needed for identification
    guest_email = models.EmailField(null=True, blank=True, verbose_name="ایمیل مهمان")

    class Meta:
        verbose_name = "جلسه گفتگو"
        verbose_name_plural = "جلسات گفتگو"
        ordering = ('-created_at',)

    def __str__(self):
        if self.user:
            user_display = self.user.get_full_name or self.user.email or self.user.phone_number
            return f"گفتگو با {user_display} ({self.id})"
        elif self.guest_email:
            return f"گفتگو با مهمان {self.guest_email} ({self.id})"
        return f"جلسه گفتگو {self.id}"

class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages', 
        verbose_name="جلسه گفتگو"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, # Messages can be from system or unassigned users initially
        verbose_name="فرستنده"
    )
    message = models.TextField(verbose_name="پیام")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="مهر زمانی")
    is_read_by_user = models.BooleanField(default=False, verbose_name="خوانده شده توسط کاربر")
    is_read_by_agent = models.BooleanField(default=False, verbose_name="خوانده شده توسط پشتیبان")

    class Meta:
        verbose_name = "پیام گفتگو"
        verbose_name_plural = "پیام‌های گفتگو"
        ordering = ('timestamp',)

    def __str__(self):
        sender_display = "سیستم"
        if self.sender:
            sender_display = self.sender.get_full_name() or self.sender.email
        return f"پیام از طرف {sender_display} در جلسه {self.session.id} در {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
