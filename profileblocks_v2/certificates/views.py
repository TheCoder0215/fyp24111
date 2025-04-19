from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Certificate, Student, DraftCertificate
from institutions.models import Institution
from certificates.forms import CertificateIssueForm
from blockchain.services.contract_service import CertificateRegistryContract
from certificates.services.issuance import confirm_certificate_from_draft
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied 
from django.db import models
from django.http import JsonResponse
import json
from certificates.forms import StudentSignupForm

def signup_view(request):
    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, "Your account has been created. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentSignupForm()
    return render(request, 'certificates/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'certificates/login.html')

def is_institution_user(user):
    return user.is_authenticated and user.user_type == 'institution'

def is_student_user(user):
    return user.is_authenticated and user.user_type == 'student'

@login_required
def dashboard_view(request):
    if request.user.user_type == 'institution':
        # support institution admin and department users
        institution = None
        inst_user = None
        if hasattr(request.user, 'institution'):
            institution = request.user.institution
        elif hasattr(request.user, 'institution_user'):
            inst_user = request.user.institution_user
            institution = inst_user.institution
        if not institution:
            messages.error(request, 'No institution associated with this user.')
            return redirect('login')
        return render(request, 'certificates/institution_dashboard.html', {
            'institution': institution,
            'institution_user': inst_user,
            'certificate_types': institution.institution_type.allowed_certificate_types
        })
    elif request.user.user_type == 'student':
        student = request.user.student
        certificates = Certificate.objects.filter(student=student)
        return render(request, 'certificates/student_dashboard.html', {
            'student': student,
            'certificates': certificates
        })
    else:
        messages.error(request, 'Invalid user type')
        return redirect('login')

@login_required
def institution_dashboard(request):
    # support institution admin and department users
    institution = getattr(request.user, 'institution', None)
    if not institution and hasattr(request.user, 'institution_user'):
        institution = request.user.institution_user.institution
    if not institution:
        messages.error(request, 'No institution found for this user')
        return redirect('dashboard')
    context = {
        'institution': institution,
        'certificate_types': institution.institution_type.allowed_certificate_types
    }
    return render(request, 'certificates/institution_dashboard.html', context)

@login_required
def student_dashboard(request):
    student = request.user.student
    certificates = Certificate.objects.filter(student=student)
    context = {
        'student': student,
        'certificates': certificates
    }
    return render(request, 'certificates/student_dashboard.html', context)

@login_required
@user_passes_test(is_institution_user)
def issue_certificate(request):
    institution = getattr(request.user, 'institution', None)
    if not institution and hasattr(request.user, 'institution_user'):
        institution = request.user.institution_user.institution
    if not institution:
        messages.error(request, "No institution associated with this user")
        return redirect('dashboard')
    if request.method == 'POST':
        form = CertificateIssueForm(request.POST, institution=institution)
        if form.is_valid():
            try:
                certificate = form.save()
                messages.success(request, 'Certificate issued successfully')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error issuing certificate: {str(e)}')
    else:
        form = CertificateIssueForm(institution=institution)
    return render(request, 'certificates/issue_certificate.html', {
        'form': form,
        'institution': institution
    })

@login_required
def review_draft(request, draft_id):
    if request.user.user_type != 'institution':
        raise PermissionDenied()
    # support institution admin and department users
    user = request.user
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution
    try:
        draft = DraftCertificate.objects.get(
            id=draft_id,
            issuing_institution=institution
        )
        return render(request, 'certificates/review_draft.html', {
            'draft': draft
        })
    except DraftCertificate.DoesNotExist:
        messages.error(request, 'Draft certificate not found')
        return redirect('issue_certificate')

@login_required
@user_passes_test(is_institution_user)
def institution_certificates(request):
    user = request.user
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution
    if institution:
        certificates = Certificate.objects.filter(
            issuing_institution=institution
        )
    else:
        certificates = Certificate.objects.none()
    # Apply filters
    certificate_type = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    if certificate_type:
        certificates = certificates.filter(certificate_type=certificate_type)
    if date_from:
        certificates = certificates.filter(created_at__gte=date_from)
    if date_to:
        certificates = certificates.filter(created_at__lte=date_to)
    if search_query:
        certificates = certificates.filter(
            models.Q(student__firstname__icontains=search_query) |
            models.Q(student__lastname__icontains=search_query) |
            models.Q(student__unique_identifier__icontains=search_query)
        )
    certificate_types = Certificate.CERTIFICATE_TYPES
    context = {
        'certificates': certificates.select_related('student', 'issuing_institution')
                                  .order_by('-created_at'),
        'certificate_types': certificate_types,
        'current_filters': {
            'type': certificate_type,
            'date_from': date_from,
            'date_to': date_to,
            'search': search_query
        }
    }
    return render(request, 'certificates/institution_certificates.html', context)

@login_required
@user_passes_test(is_institution_user)
def certificate_details(request, cert_id):
    user = request.user
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution
    cert = get_object_or_404(
        Certificate.objects.select_related('student', 'issuing_institution'),
        id=cert_id,
        issuing_institution=institution
    )
    return render(request, 'certificates/certificate_details_modal.html', {
        'cert': cert
    })

@login_required
@user_passes_test(is_student_user)
def student_certificates(request):
    certificates = Certificate.objects.filter(
        student__user=request.user
    ).select_related('issuing_institution').order_by('-created_at')
    certificates_data = [{
        'cert_hash': cert.certificate_hash,
        'signed_hash': cert.signed_hash,
        'type': cert.certificate_type,
        'institution': cert.issuing_institution.name,
        'date_issued': cert.created_at,
        'metadata': cert.metadata
    } for cert in certificates]
    return render(request, 'certificates/student_certificates.html', {
        'certificates': certificates_data
    })

@login_required
def confirm_certificate(request, draft_id):
    user = request.user
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution
    if user.user_type != 'institution':
        raise PermissionDenied()
    if request.method != 'POST':
        return redirect('issue_certificate')
    try:
        draft = DraftCertificate.objects.get(
            id=draft_id,
            issuing_institution=institution
        )
        certificate = confirm_certificate_from_draft(draft)
        messages.success(request, 'Certificate issued successfully')
        return redirect('dashboard')
    except DraftCertificate.DoesNotExist:
        messages.error(request, 'Draft certificate not found')
    except Exception as e:
        messages.error(request, f'Error issuing certificate: {str(e)}')
    return redirect('issue_certificate')

@login_required
@user_passes_test(is_institution_user)
def lookup_student(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student = Student.objects.get(
                models.Q(unique_identifier=student_id) |
                models.Q(user__unique_identifier=student_id)
            )
            return JsonResponse({
                'success': True,
                'student': {
                    'name': f"{student.firstname} {student.lastname}",
                    'identifier': student.unique_identifier
                }
            })
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def logout_view(request):
    logout(request)
    return redirect('login')