from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Category  # Assuming Product and Category models
from .models import ProductReview
from decimal import Decimal

User = get_user_model()

class ReviewViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='reviewer@example.com', phone_number='09444444444', password='password123')
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.product = Product.objects.create(
            name='Test Product for Review',
            slug='test-product-review',
            category=self.category,
            price=Decimal('50.00'),
            stock=10
        )
        self.add_review_url = reverse('reviews:add_review', kwargs={'product_slug': self.product.slug})

    def test_add_review_redirects_anonymous_user(self):
        """Tests that anonymous users are redirected from the add review page."""
        response = self.client.get(self.add_review_url)
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.add_review_url}")

    def test_add_review_page_loads_for_authenticated_user(self):
        """Tests that the add review page loads for authenticated users."""
        self.client.login(email='reviewer@example.com', password='password123')
        response = self.client.get(self.add_review_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name) # Check if product name is on the page

    def test_add_review_submission_creates_review_and_redirects(self):
        """Tests that submitting a valid review creates a ProductReview object and redirects."""
        self.client.login(email='reviewer@example.com', password='password123')
        review_data = {
            'rating': 5,
            'comment': 'This is an excellent product!'
        }
        response = self.client.post(self.add_review_url, review_data)

        self.assertEqual(response.status_code, 302) # Expect redirect after successful submission
        self.assertRedirects(response, reverse('products:product_detail', kwargs={'slug': self.product.slug}))

        self.assertEqual(ProductReview.objects.count(), 1)
        review = ProductReview.objects.first()
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'This is an excellent product!')
        # By default, reviews might be pending approval depending on model logic
        # self.assertEqual(review.status, ProductReview.STATUS_APPROVED) # Or STATUS_PENDING

    def test_add_review_submission_fails_with_invalid_data(self):
        """Tests that submitting an invalid review (e.g., no rating) shows errors."""
        self.client.login(email='reviewer@example.com', password='password123')
        invalid_review_data = {
            'comment': 'This review has no rating.'
            # Missing 'rating'
        }
        response = self.client.post(self.add_review_url, invalid_review_data)

        self.assertEqual(response.status_code, 200) # Should re-render the form with errors
        # Make sure the form is passed in the context with the name 'form'
        self.assertIn('form', response.context)
        form_in_context = response.context['form']
        # The actual error message from the form is "لطفاً یک امتیاز انتخاب کنید."
        self.assertFormError(form_in_context, 'rating', 'لطفاً یک امتیاز انتخاب کنید.')
        self.assertEqual(ProductReview.objects.count(), 0) # No review should be created
