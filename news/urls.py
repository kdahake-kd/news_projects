"""
URL configuration for the news search application.

This module defines URL routes for both news-related views and user authentication views.
It maps each URL path to the corresponding view function or class-based view.

Routes:
    - '' (search_news): Homepage for searching news by keyword.
    - 'history/' (search_history): Displays the user's search history and previously fetched articles.
    - 'refresh/<int:keyword_id>/' (refresh_news): Fetches and updates new articles for a specific keyword.

Authentication Routes:
    - 'login/' (custom_login_view): Handles user login.
    - 'register/' (register_view): Handles user registration.
    - 'logout/' (LogoutView): Logs out the user and redirects to the login page.

Each view is responsible for user-specific data and requires appropriate authentication where needed.

"""

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.search_news, name='search_news'),
    path('history/', views.search_history, name='search_history'),
    path('refresh/<int:keyword_id>/', views.refresh_news, name='refresh_news'),


    # Auth Views
    path('login/', views.custom_login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.user_logout_view, name='logout'),
]
