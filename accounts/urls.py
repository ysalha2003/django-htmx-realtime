from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Enhanced validation endpoints for registration
    path('validate/username/', views.validate_username, name='validate_username'),
    path('validate/first-name/', views.validate_first_name, name='validate_first_name'),
    path('validate/last-name/', views.validate_last_name, name='validate_last_name'),
    path('validate/email/', views.validate_email_register, name='validate_email'),
    path('validate/password/', views.validate_password, name='validate_password'),
    path('validate/password2/', views.validate_password2, name='validate_password2'),
    
    # New validation endpoints for login and password reset
    path('validate/login-username/', views.validate_login_username, name='validate_login_username'),
    path('validate/password-reset-email/', views.validate_password_reset_email, name='validate_password_reset_email'),
]
