from django.test import TestCase
from .models import Discount, Campaign
from products.models import Product, Category  # Assuming Product and Category models exist
from decimal import Decimal
from django.utils import timezone
import datetime

class DiscountModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00')
        )

    def test_create_percentage_discount(self):
        """Tests creation of a percentage-based discount."""
        discount = Discount.objects.create(
            name='10% Off All', # Changed name as it's not category specific anymore
            code='PERCENT10', # Added required code field
            discount_type='percentage', # Use string literal
            value=Decimal('10.00'),
            # applicable_to=Discount.APPLICABLE_TO_CATEGORY, # Field does not exist
            # category=self.category, # Field does not exist
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=30)
        )
        self.assertEqual(discount.name, '10% Off All')
        self.assertEqual(discount.value, Decimal('10.00'))
        self.assertTrue(discount.is_active) # Access as attribute

    def test_create_fixed_amount_discount_for_product(self):
        """Tests creation of a fixed amount discount (now generic, not product-specific in model)."""
        discount = Discount.objects.create(
            name='Save $5 Generic', # Changed name
            code='FIXED5', # Added required code field
            discount_type='fixed_amount', # Use string literal
            value=Decimal('5.00'),
            # applicable_to=Discount.APPLICABLE_TO_PRODUCT, # Field does not exist
            # product=self.product, # Field does not exist
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=30)
        )
        self.assertEqual(discount.name, 'Save $5 Generic')
        self.assertEqual(discount.value, Decimal('5.00'))
        self.assertTrue(discount.is_active) # Access as attribute

class CampaignModelTestCase(TestCase):
    def test_create_campaign(self):
        """Tests creation of a campaign."""
        campaign = Campaign.objects.create(
            name='Summer Sale',
            description='Big summer sale!',
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=60)
        )
        self.assertEqual(campaign.name, 'Summer Sale')
        self.assertTrue(campaign.is_active) # Access as attribute

    # Add more tests for campaign logic, e.g., associating discounts
