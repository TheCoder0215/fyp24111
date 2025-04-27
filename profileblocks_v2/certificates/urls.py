#certificates/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('manage/', views.manage_certificates, name='manage_certificates'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/certificates/<str:certificate_hash>/', views.student_certificate_detail, name='student_certificate_detail'),
    path('issue/', views.issue_certificate, name='issue_certificate'),
    path('all-certificates/', views.student_certificates, name='student_certificates'),
    path('lookup-student/', views.lookup_student, name='lookup_student'),
    path('issued-certificates/', views.institution_certificates, name='institution_certificates'),
    path('details/<str:certificate_hash>/', views.certificate_details, name='certificate_details'),
    path('db-verify/', views.db_verify_view, name='db_verify'),
    path('chain-verify/', views.chain_verify_view, name='chain_verify'),
    path('db-signature-verify/', views.db_signature_verify_view, name='db_signature_verify'),
    path('full-verify/', views.full_verification_view, name='full_verification'),
]