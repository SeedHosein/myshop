from django.test import TestCase
from django.urls import reverse
from .models import StaticPage

class StaticPageViewsTestCase(TestCase):
    def setUp(self):
        self.static_page = StaticPage.objects.create(
            title='About Us',
            slug='about-us',
            content='This is the about us page content.',
            is_published=True
        )
        self.static_page_url = reverse('static_pages:static_page_detail', kwargs={'slug': self.static_page.slug})

    def test_static_page_detail_view_loads_published_page(self):
        """Tests that a published static page loads correctly."""
        response = self.client.get(self.static_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.static_page.title)
        self.assertContains(response, self.static_page.content)

    def test_static_page_detail_view_unpublished_page_returns_404(self):
        """Tests that an unpublished static page returns a 404 error."""
        unpublished_page = StaticPage.objects.create(
            title='Draft Page',
            slug='draft-page',
            content='This is a draft page.',
            is_published=False # Ensure it's not published
        )
        response = self.client.get(reverse('static_pages:static_page_detail', kwargs={'slug': unpublished_page.slug}))
        self.assertEqual(response.status_code, 404)

    def test_static_page_detail_view_non_existent_slug_returns_404(self):
        """Tests that accessing a static page with a non-existent slug returns a 404."""
        response = self.client.get(reverse('static_pages:static_page_detail', kwargs={'slug': 'non-existent-page'}))
        self.assertEqual(response.status_code, 404)
