from django.test import TestCase
from django.urls import reverse

class AccountsViewsTestCase(TestCase):
    def test_login_page_loads_correctly(self):
        """Tests that the login page loads with a 200 status code."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads_correctly(self):
        """Tests that the register page loads with a 200 status code."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
