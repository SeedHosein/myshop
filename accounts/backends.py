# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserProfile = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    """
    Custom authentication backend.

    Allows users to log in using their email address or phone number.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Overrides the authenticate method to allow login with email or phone number.
        The 'username' parameter here is what the user enters in the login form field
        (which we labeled 'Email or Phone Number').
        """
        if username is None:
            # If called from UserLoginForm, username is the first argument.
            # If called directly, it might be passed as a keyword argument.
            username = kwargs.get(UserProfile.USERNAME_FIELD)
            if username is None:
                 # Fallback if it was passed as 'phone_number' directly (less common)
                username = kwargs.get('phone_number')

        if username is None:
            return None # No identifier provided

        try:
            # Try to fetch the user by looking up the identifier in email OR phone_number fields.
            # Q objects are used for OR queries.
            user = UserProfile.objects.get(Q(email__iexact=username) | Q(phone_number=username))
        except UserProfile.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between a user not existing and a user existing but
            # having an incorrect password.
            UserProfile().set_password(password)
            return None
        except UserProfile.MultipleObjectsReturned:
            # This shouldn't happen if email and phone_number are unique, but as a safeguard:
            return None 

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        """
        Overrides the get_user method to retrieve a user by their ID.
        """
        try:
            return UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            return None 