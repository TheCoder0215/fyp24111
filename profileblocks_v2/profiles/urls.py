#profiles/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_profiles, name='certificate_profiles'),
    path('create/', views.create_profile_select, name='create_profile_select'),
    path('create/confirm/', views.create_profile_confirm, name='create_profile_confirm'),
    path('<str:profile_id>/delete/', views.delete_profile, name='delete_profile'),
    path('<str:profile_id>/view/', views.view_profile, name='view_profile'),
    path('<str:profile_id>/share/', views.export_profile_share, name='export_profile_share'),
]