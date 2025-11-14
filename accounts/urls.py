from django.contrib.auth.views import LogoutView
from django.urls import path
from accounts.views import *

app_name = 'accounts'
urlpatterns = [
    path('signin/', LoginView.as_view(), name='signin'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
]