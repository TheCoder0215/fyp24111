from django.urls import path
from . import views

urlpatterns = [
    path('profile_verification/<str:signed_hash>/', views.verify_profile, name='verify_profile'),
    path('certificate-verify/', views.public_certificate_verification, name='public_certificate_verification'),
    path('certificate-verify/db-signature/', views.public_db_signature_verify, name='public_db_signature_verify'),
    path('certificate-verify/full/', views.public_full_verification, name='public_full_verification'),
    path('', views.landing, name='landing'),
]