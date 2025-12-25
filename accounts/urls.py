# This is a new file: accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'  # Application namespace

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='profile_update'),

    path('password/change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', views.UserPasswordChangeDoneView.as_view(), name='password_change_done'),

    path('password/reset/', views.UserPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.UserPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.UserPasswordResetCompleteView.as_view(), name='password_reset_complete'),
] 