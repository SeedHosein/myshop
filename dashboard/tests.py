from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardViewsTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from core.models import CorePermissions # Assuming CorePermissions is where 'view_dashboard' is defined
        from products.models import Product # Needed for content type

        from django.contrib.auth.models import Group

        # Ensure unique phone numbers for each user to avoid IntegrityError
        self.user = User.objects.create_user(email='testuser_dashboard@example.com', phone_number='09111111111', password='password123')
        self.staff_user = User.objects.create_user(email='staff_dashboard@example.com', phone_number='09222222222', password='password123', is_staff=True, is_active=True)

        # Create a group and assign permissions to the group
        staff_group, created = Group.objects.get_or_create(name='Test Staff Group')

        permissions_to_add = []
        try:
            view_dashboard_perm = Permission.objects.get(content_type__app_label='core', codename='view_dashboard')
            permissions_to_add.append(view_dashboard_perm)
        except Permission.DoesNotExist:
            print("CRITICAL: Permission 'core.view_dashboard' NOT FOUND.")

        try:
            view_product_perm = Permission.objects.get(content_type__app_label='products', codename='view_product')
            permissions_to_add.append(view_product_perm)
        except Permission.DoesNotExist:
            print("CRITICAL: Permission 'products.view_product' NOT FOUND.")

        if permissions_to_add:
            staff_group.permissions.add(*permissions_to_add)

        self.staff_user.groups.add(staff_group)

        # Refresh user from DB to ensure permissions/groups are reloaded for the test client session
        self.staff_user = User.objects.get(pk=self.staff_user.pk)

    def test_dashboard_home_redirects_non_staff(self):
        """Tests that non-staff users are redirected from the dashboard home."""
        self.client.login(email='testuser@example.com', password='password123')
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertEqual(response.status_code, 302)
        # Assuming redirect to login. A more specific check might be needed
        # if there's a custom 'access denied' page.
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:dashboard_home')}")


    def test_dashboard_home_loads_for_staff(self):
        """Tests that the dashboard home loads for staff users."""
        self.client.login(email=self.staff_user.email, password='password123')
        response = self.client.get(reverse('dashboard:dashboard_home'))
        self.assertEqual(response.status_code, 200)

    # Add more tests for other dashboard views, e.g., product list, order list, etc.
    # Example for product list:
    def test_dashboard_product_list_loads_for_staff(self):
        """Tests that the dashboard product list loads for staff users."""
        self.client.login(email=self.staff_user.email, password='password123')
        response = self.client.get(reverse('dashboard:product_list')) # Assuming this is the correct URL name
        self.assertEqual(response.status_code, 200)

    def test_dashboard_product_list_redirects_non_staff(self):
        """Tests that non-staff users are redirected from dashboard product list."""
        self.client.login(email='testuser@example.com', password='password123')
        response = self.client.get(reverse('dashboard:product_list'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:product_list')}")
