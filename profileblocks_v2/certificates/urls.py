#certificates/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('issue/', views.issue_certificate, name='issue_certificate'),
    path('all-certificates/', views.student_certificates, name='student_certificates'),
    path('lookup-student/', views.lookup_student, name='lookup_student'),
    path('issued-certificates/', views.institution_certificates, name='institution_certificates'),
    path('certificates/details/<int:cert_id>/', views.certificate_details, name='certificate_details')
]