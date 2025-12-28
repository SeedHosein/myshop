import secrets
import re
import time

from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib.auth import login, logout
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    LogoutView as AuthLogoutView,
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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection
from django.utils.translation import gettext_lazy as _ # Added for messages

from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    UserProfileUpdateForm,
    CustomPasswordChangeForm,      # New custom form
    CustomPasswordResetForm,       # New custom form
    CustomSetPasswordForm          # New custom form
)
from .models import UserProfile
# Assuming you have Order model in cart_and_orders app
from cart_and_orders.models import Order


class UserRegisterView(SuccessMessageMixin, View):
    model = UserProfile
    template_name = 'accounts/register.html'
    form_class = UserRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('accounts:profile'))
        
        if request.session.get('otp_verification_data', ''):
            del request.session['otp_verification_data']
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, form=None):
        if form is None:
            form = self.form_class()
        return render(request, self.template_name, {
            'SHOP_NAME': settings.SHOP_NAME,
            'form': form
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if not form.is_valid():
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.label}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
            # Pass the form back to get with its errors and pre-filled data
            return self.get(request, form=form)

        # Form is valid, proceed with OTP logic
        username = form.cleaned_data['username'] # This is now normalized email or phone number
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        password = form.cleaned_data['password']
        
        # input_type and destination are set by clean_username in the form
        input_type = form.input_type
        destination = form.destination
        
        # Rate Limiting based on IP + destination
        ip = self.get_client_ip(request)
        rate_key = f"otp_rate:{ip}:{destination}"
        user_data_key = f"user_data:{destination}"
        current_time = int(time.time())

        # Get a list of previous requests
        requests = cache.get(rate_key, [])
        if not isinstance(requests, list):
            requests = []

        # Delete requests older than 10 minutes
        requests = [ts for ts in requests if ts > current_time - 600]

        if len(requests) >= 7:
            messages.error(self.request, "تعداد درخواست‌های شما زیاد است. لطفاً 10 دقیقه دیگر دوباره تلاش کنید.")
            return self.get(request, form=form)
        
        
        redis_client = get_redis_connection("default")
        
        # Temporary lock check (120 seconds after previous request)
        time_lose_code = redis_client.ttl(user_data_key)
        if time_lose_code > 0:
            messages.error(self.request, f"لطفاً {time_lose_code} ثانیه صبر کنید و دوباره تلاش کنید.")
            return self.get(request, form=form)
        
        # Add new request
        requests.append(current_time)
        cache.set(rate_key, requests, timeout=600)
        
        # Generate a secure 6-digit code
        code = ''.join(secrets.choice('0123456789') for _ in range(6))

        # Store in Redis hash (valid for 2 minutes)
        redis_client.hset(user_data_key, mapping={
            'otp_code': code,
            'attempts': '0',
            'first_name': first_name,
            'last_name': last_name,
            'password': password,
            'input_type': input_type,
        })
        redis_client.expire(user_data_key, 120)  # 2 minutes credit


        # message for send otp code
        message = (
            f"{settings.SHOP_NAME}\n"
            f"کد تأیید شما: {code}\n"
            f"این کد فقط ۲ دقیقه معتبر است.\n"
            f"هشدار: این کد را در اختیار شخص دیگری قرار ندهید."
        )
        # print(f"----------------code: {code}---------------")
        
        if input_type == 'email':
            send_mail(
                subject=f'کد تأیید ثبت‌نام در {settings.SHOP_NAME}',
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[destination],
                fail_silently=False,
            )
        elif input_type == 'mobile':
            # TODO: Send real SMS (e.g. with Kavenegar or Twilio or more)
            pass
        
        # Redirect to confirmation page (we pass the destination in secret)
        masked_destination = self.mask_destination(destination, input_type)
        messages.success(
            request, 
            f"کد تأیید به { 'شماره موبایل' if input_type == 'mobile' else 'ایمیل' } { masked_destination } شما ارسال شد."
            )
        
        request.session['otp_verification_data'] = {
            'destination': destination,
            'input_type': input_type,
            'masked_destination': masked_destination,
        }

        return redirect('accounts:verify_otp')
        
    def get_client_ip(self, request):
        """Get the user's real IP (even behind a proxy)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def mask_destination(self, destination, input_type):
        """Masked display of email or mobile number for security and better UX"""
        if input_type == 'email':
            local, domain = destination.split('@')
            return f"{local[:3]}***@{domain}"
        else:  # mobile
            return f"******{destination[-4:]}"
        

class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'
    model = UserProfile

    def get(self, request):
        # If you are taken directly to the page without session data, return to registration.
        verification_data = request.session.get('otp_verification_data')
        if not verification_data:
            messages.error(request, "کد تایید شما منقضی شده است. لطفاً دوباره ثبت‌نام کنید.")
            return redirect('accounts:register')
        
        time_lose_code = get_redis_connection("default").ttl(f"user_data:{verification_data['destination']}")
        if time_lose_code < 1:
            if 'otp_verification_data' in request.session:
                del request.session['otp_verification_data']
            messages.error(request, "کد تایید شما منقضی شده است. لطفاً دوباره ثبت‌نام کنید.")
            return redirect('accounts:register')

        
        return render(request, self.template_name, {
            'SHOP_NAME': settings.SHOP_NAME,
            'time_lose_code': time_lose_code,
            'username': verification_data['masked_destination'],
            'input_type': 'شماره موبایل' if verification_data['input_type'] == 'mobile' else 'ایمیل',
        })

    def post(self, request):
        verification_data = request.session.get('otp_verification_data')
        if not verification_data:
            messages.error(request, "کد تایید شما منقضی شده است. لطفاً دوباره درخواست دهید.")
            return redirect('accounts:register')

        destination = verification_data['destination']
        input_type = verification_data['input_type']

        # Collect OTP code from 6 separate fields (otp_1 to otp_6)
        otp_parts = []
        for i in range(1, 7):
            digit = request.POST.get(f'otp_{i}', '').strip()
            if not digit.isdigit():
                messages.error(request, "کد وارد شده نامعتبر است.")
                return self.get(request)
            otp_parts.append(digit)

        entered_code = ''.join(otp_parts)

        if not entered_code or len(entered_code) != 6:
            messages.error(request, "لطفاً کد ۶ رقمی را کامل وارد کنید.")
            return self.get(request)

        user_data_key = f"user_data:{destination}"
        redis_client = get_redis_connection("default")

        user_data = redis_client.hgetall(user_data_key)

        if not user_data:
            messages.error(request, "کد تایید شما منقضی شده است. لطفاً دوباره درخواست دهید.")
            del request.session['otp_verification_data']
            return redirect('accounts:register')

        # Convert bytes to strings
        stored_code = user_data.get(b'otp_code', b'').decode('utf-8')
        attempts = int(user_data.get(b'attempts', b'0').decode('utf-8'))

        if attempts >= 5:
            redis_client.delete(user_data_key)
            del request.session['otp_verification_data']
            messages.error(request, "تعداد تلاش‌های ناموفق بیش از حد مجاز بود. لطفاً دوباره ثبت‌نام کنید.")
            return redirect('accounts:register')

        if entered_code == stored_code:
            # valid otp code - create user
            first_name = user_data[b'first_name'].decode('utf-8')
            last_name = user_data[b'last_name'].decode('utf-8')
            password = user_data[b'password'].decode('utf-8')

            # Create user based on input type
            if input_type == 'email':
                user = UserProfile.objects.create_user(
                    email=destination,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
            else: # mobile
                user = UserProfile.objects.create_user(
                    phone_number=destination,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

            # Automatic login
            login(request, user, backend='accounts.backends.EmailOrPhoneBackend')

            # Clear cache data
            redis_client.delete(user_data_key)
            if 'otp_verification_data' in request.session:
                del request.session['otp_verification_data']

            messages.success(request, "ثبت‌نام با موفقیت انجام شد. خوش آمدید!")
            return redirect(reverse_lazy('core:home'))

        else:
            # invalid otp code
            attempts += 1
            redis_client.hset(user_data_key, 'attempts', str(attempts))
            messages.error(request, f"کد وارد شده اشتباه است. {5 - attempts} تلاش باقی‌مانده.")
            return self.get(request)

class UserLoginView(AuthLoginView):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'
    # LOGIN_REDIRECT_URL will be used from settings.py by default
    # Or you can set success_url here: success_url = reverse_lazy('some_page')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('accounts:profile'))
        return super().dispatch(request, *args, **kwargs)
    
    # Add a message for failed login
    def form_invalid(self, form):
        messages.error(self.request, "نام کاربری (آدرس ایمیل/شماره موبایل) یا رمز عبور اشتباه است. لطفا دوباره تلاش کنید.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context

class UserLogoutView(AuthLogoutView):
    # LOGOUT_REDIRECT_URL will be used from settings.py by default
    # Or you can set next_page here: 
    next_page = reverse_lazy('core:home') # Assuming you have a 'home' url pattern
    # template_name = 'accounts/logout.html' # Optional: a page confirming logout

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
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, "رمز عبور شما با موفقیت تغییر کرد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SHOP_NAME'] = settings.SHOP_NAME
        return context


# Password Reset Views
class UserPasswordResetView(AuthPasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/password_reset_email.html' 
    subject_template_name = 'accounts/password_reset_subject.txt' 
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
    form_class = CustomSetPasswordForm
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
