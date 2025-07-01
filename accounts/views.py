from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib.auth import login, logout # Import login directly
from django.contrib.auth.views import (
    LoginView as AuthLoginView, # Rename to avoid clash
    LogoutView as AuthLogoutView, # Rename to avoid clash
    PasswordChangeView as AuthPasswordChangeView,
    PasswordResetView as AuthPasswordResetView,
    PasswordResetDoneView as AuthPasswordResetDoneView,
    PasswordResetConfirmView as AuthPasswordResetConfirmView,
    PasswordResetCompleteView as AuthPasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin # For success messages
from django.contrib import messages # For manual messages
from django.conf import settings

from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm
from .models import UserProfile
# Assuming you have Order model in cart_and_orders app
from cart_and_orders.models import Order 

class UserRegisterView(SuccessMessageMixin, CreateView):
    model = UserProfile
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:profile') # Redirect to profile page after registration
    success_message = "ثبت نام شما با موفقیت انجام شد. خوش آمدید!"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        response = super().form_valid(form)
        # Log the user in after successful registration
        user = self.object # The new user object
        login(self.request, user, backend='accounts.backends.EmailOrPhoneBackend') # Automatically log in the user
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserLoginView(AuthLoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    # LOGIN_REDIRECT_URL will be used from settings.py by default
    # Or you can set success_url here: success_url = reverse_lazy('some_page')
    # Add a message for failed login
    def form_invalid(self, form):
        messages.error(self.request, "نام کاربری (ایمیل/تلفن) یا رمز عبور اشتباه است. لطفا دوباره تلاش کنید.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserLogoutView(AuthLogoutView):
    # LOGOUT_REDIRECT_URL will be used from settings.py by default
    # Or you can set next_page here: next_page = reverse_lazy('home') # Assuming you have a 'home' url pattern
    template_name = 'accounts/logout.html' # Optional: a page confirming logout

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, "شما با موفقیت خارج شدید.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context


class UserProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        # Return the currently logged-in user's profile
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Example: Add user's order history
        try:
            context['orders'] = Order.objects.filter(user=self.request.user).order_by('-order_date')[:10]
        except ImportError:
            context['orders'] = [] # In case Order model is not yet available or imported
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')
    success_message = "پروفایل شما با موفقیت بروزرسانی شد."

    def get_object(self, queryset=None):
        # Ensure users can only update their own profile
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

# Password Change Views
class UserPasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    template_name = 'accounts/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done') # Django provides a PasswordChangeDoneView by default
    success_message = "رمز عبور شما با موفقیت تغییر کرد."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

# Django provides PasswordChangeDoneView automatically if you set success_url in PasswordChangeView
# but if you want a custom template or message for it, you create it:
from django.contrib.auth.views import PasswordChangeDoneView as AuthPasswordChangeDoneView
class UserPasswordChangeDoneView(LoginRequiredMixin, AuthPasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # messages.success(self.request, "رمز عبور شما با موفقیت تغییر کرد.") # Message is now in PasswordChangeView
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context


# Password Reset Views
# These generally use Django's built-in forms (PasswordResetForm, SetPasswordForm)
# PasswordResetForm uses the email field to find users.
class UserPasswordResetView(AuthPasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html' # You need to create this email template
    subject_template_name = 'accounts/password_reset_subject.txt' # And this subject template
    success_url = reverse_lazy('accounts:password_reset_done')
    from_email = 'noreply@myshop.com' # Replace with your actual sending email
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserPasswordResetDoneView(AuthPasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserPasswordResetConfirmView(AuthPasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserPasswordResetCompleteView(AuthPasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context
