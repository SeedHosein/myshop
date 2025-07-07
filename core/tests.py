from django.test import TestCase
from django.urls import reverse

class CoreViewsTestCase(TestCase):
    def test_home_page_loads_correctly(self):
        """Tests that the home page loads with a 200 status code."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    # If there are other core views like 'about_us' or 'contact_us'
    # that don't require authentication, they can be tested similarly.
    # For example:
    # def test_about_us_page_loads_correctly(self):
    #     response = self.client.get(reverse('core:about_us')) # Assuming URL name is 'about_us'
    #     self.assertEqual(response.status_code, 200)
