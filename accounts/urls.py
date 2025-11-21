from django.contrib.auth.views import LogoutView
from django.urls import path
from accounts.views import *

app_name = 'accounts'
urlpatterns = [
    path('signin/', LoginView.as_view(), name='signin'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset_confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]