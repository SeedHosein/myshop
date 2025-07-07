from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class CartAndOrdersViewsTestCase(TestCase):
    def setUp(self):
        # Create a user for authentication if needed for some views
        self.user = User.objects.create_user(email='testuser_cart@example.com', phone_number='09333333333', password='password123')
        # Need a product to add to the cart for some tests
        from products.models import Category, Product # Assuming these models
        from decimal import Decimal
        self.category = Category.objects.create(name='Test Cart Category', slug='test-cart-cat')
        self.product = Product.objects.create(
            name='Test Cart Product',
            slug='test-cart-prod',
            category=self.category,
            price=Decimal('10.00'),
            stock=10
        )

    def test_cart_detail_view_loads_correctly_for_anonymous_user(self):
        """Tests that the cart detail page loads with a 200 status code for anonymous users."""
        response = self.client.get(reverse('cart_and_orders:cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_checkout_view_redirects_anonymous_user(self):
        """Tests that the checkout page redirects anonymous users to login."""
        response = self.client.get(reverse('cart_and_orders:checkout'))
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('cart_and_orders:checkout')}")

    def test_checkout_view_loads_for_authenticated_user(self):
        """Tests that the checkout page loads with a 200 status code for authenticated users if cart is not empty."""
        self.client.login(email='testuser_cart@example.com', password='password123')

        # Add an item to the cart first
        from .models import Cart, CartItem
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        cart.save() # Ensure cart totals are updated if model logic depends on it

        response = self.client.get(reverse('cart_and_orders:checkout'))
        self.assertEqual(response.status_code, 200)

    def test_checkout_view_redirects_authenticated_user_if_cart_empty(self):
        """Tests checkout redirects authenticated users to products page if cart is empty."""
        self.client.login(email='testuser_cart@example.com', password='password123')
        # Ensure cart is empty
        from .models import Cart
        cart, _ = Cart.objects.get_or_create(user=self.user)
        cart.items.all().delete() # Clear any items
        cart.save()

        response = self.client.get(reverse('cart_and_orders:checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('products:product_list'))
