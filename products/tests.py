from django.test import TestCase
from django.urls import reverse
from .models import Category, Product
from decimal import Decimal

class ProductViewsTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            description_short='Short description',
            stock=10
        )

    def test_product_list_page_loads_correctly(self):
        """Tests that the product list page loads with a 200 status code."""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_detail_page_loads_correctly(self):
        """Tests that the product detail page for an existing product loads with a 200 status code."""
        response = self.client.get(reverse('products:product_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.product.description_short)

    def test_product_detail_page_for_invalid_slug_returns_404(self):
        """Tests that accessing a product detail page with an invalid slug returns a 404."""
        response = self.client.get(reverse('products:product_detail', kwargs={'slug': 'non-existent-product'}))
        self.assertEqual(response.status_code, 404)

    def test_product_list_by_category_page_loads_correctly(self):
        """Tests that the product list page filtered by category loads correctly."""
        response = self.client.get(reverse('products:category_detail', kwargs={'category_slug': self.category.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        # Check that products not in this category are not listed (if any were created)

        # Create another category and product to ensure filtering works
        other_category = Category.objects.create(name='Other Category', slug='other-category')
        other_product = Product.objects.create(
            name='Other Product',
            slug='other-product',
            category=other_category,
            price=Decimal('10.00'),
            stock=5
        )
        response = self.client.get(reverse('products:category_detail', kwargs={'category_slug': self.category.slug}))
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, other_product.name)
