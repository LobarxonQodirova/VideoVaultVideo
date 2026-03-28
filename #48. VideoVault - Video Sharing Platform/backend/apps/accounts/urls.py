"""
URL patterns for the accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/<str:username>/", views.PublicProfileView.as_view(), name="public-profile"),
    path("password/change/", views.ChangePasswordView.as_view(), name="change-password"),
    path("users/", views.UserListView.as_view(), name="user-list"),
]
