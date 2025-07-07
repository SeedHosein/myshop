from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', phone_number='09123456789', password='password123')
        self.staff_user = User.objects.create_user(email='staff@example.com', phone_number='09123456788', password='password123', is_staff=True)

    def test_support_chat_dashboard_redirects_non_staff(self):
        """Tests that non-staff users are redirected from the support chat dashboard."""
        self.client.login(email='testuser@example.com', password='password123')
        response = self.client.get(reverse('chat:support_dashboard'))
        # User is authenticated but not staff, UserPassesTestMixin raises PermissionDenied (403)
        self.assertEqual(response.status_code, 403)


    def test_support_chat_dashboard_loads_for_staff(self):
        """Tests that the support chat dashboard loads for staff users."""
        self.client.login(email='staff@example.com', password='password123')
        response = self.client.get(reverse('chat:support_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_chat_room_redirects_anonymous_user(self):
        """Tests that anonymous users are redirected from chat rooms."""
        # Assuming chat_session_id is a required parameter for the chat room URL
        # and a valid session ID would be needed. For this basic test,
        # we'll use a placeholder. A more robust test would create a ChatSession.
        # We also need a valid UUID for the session_id
        import uuid
        test_uuid = uuid.uuid4()
        chat_room_url = reverse('chat:chat_room_with_id', kwargs={'session_id': test_uuid})
        response = self.client.get(chat_room_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={chat_room_url}")

    # A more comprehensive test would involve creating a ChatSession and testing
    # if an authenticated user can access their chat room.
    # For now, this covers basic view accessibility.
