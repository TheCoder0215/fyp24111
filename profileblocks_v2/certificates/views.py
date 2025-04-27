# certificates/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied 
from django.db import models
from django.http import JsonResponse
from .models import Certificate, Student, DraftCertificate
from certificates.forms import CertificateIssueForm, StudentSignupForm
from certificates.services.issuance import confirm_certificate_from_draft, issue_certificate_service
from certificates.services.verification import verify_certificate_full

import json

# Helper function to check if the user is an authenticated student
def is_student_user(user):
    return user.is_authenticated and user.user_type == 'student'

# Helper function to check if the user is an authenticated institution user
def is_institution_user(user):
    return user.is_authenticated and user.user_type == 'institution'

@login_required  # Require login to access this view
@user_passes_test(lambda u: u.is_authenticated and u.user_type == 'student')  # Only allow students
def student_profile(request):
    student = request.user.student  # Get the student profile linked to the logged-in user
    return render(request, 'certificates/student_profile.html', {'student': student})  # Render profile page

@login_required
@user_passes_test(is_student_user)  # Only students can view their certificate details
def student_certificate_detail(request, certificate_hash):
    student = request.user.student
    # Get the certificate by hash and ensure it belongs to the logged-in student
    cert = get_object_or_404(Certificate, certificate_hash=certificate_hash, student=student)
    return render(request, 'certificates/student_certificate_detail.html', {
        'cert': cert
    })

@login_required
@user_passes_test(is_student_user)  # Only students can view their certificates list
def student_certificates(request):
    # Query certificates for the logged-in student, join issuing institution data for efficiency
    certificates = Certificate.objects.filter(
        student__user=request.user
    ).select_related('issuing_institution').order_by('-created_at')
    return render(request, 'certificates/student_certificates.html', {
        'certificates': certificates
    })

@login_required
def manage_certificates(request):
    # Get certificates of the logged-in student
    certificates = Certificate.objects.filter(student=request.user.student)
    # Check if each certificate has associated profiles
    cert_profiles = {cert.id: cert.certificateprofile_set.exists() for cert in certificates}

    if request.method == "POST":
        # Iterate through certificates to update their public visibility
        for cert in certificates:
            is_checked = request.POST.get(f'public_{cert.id}') == "on"  # Checkbox state
            # Only update if profile does not exist and visibility changed
            if not cert_profiles[cert.id]:
                if cert.is_public != is_checked:
                    cert.is_public = is_checked
                    cert.save()  # Save changes to DB
        return redirect('manage_certificates')  # Redirect to refresh page

    # Render the manage certificates page with current certificates and profiles
    return render(request, 'certificates/manage_certificates.html', {
        'certificates': certificates,
        'cert_profiles': cert_profiles,
    })

def signup_view(request):
    if request.method == "POST":
        form = StudentSignupForm(request.POST)  # Bind form data
        if form.is_valid():
            student = form.save()  # Save new student user
            messages.success(request, "Your account has been created. Please log in.")
            return redirect('login')  # Redirect to login page after signup
        else:
            messages.error(request, "Please correct the errors below.")  # Show form errors
    else:
        form = StudentSignupForm()  # Display empty signup form initially
    return render(request, 'certificates/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Get username and password from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)  # Authenticate user
        if user is not None and user.is_active:
            login(request, user)  # Log the user in
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, 'Invalid credentials')  # Show error for invalid login
    return render(request, 'certificates/login.html')  # Render login form

@login_required
def dashboard_view(request):
    # Render dashboard depending on user type
    if request.user.user_type == 'institution':
        # Institution users (admins or department users)
        institution = None
        inst_user = None
        # Determine associated institution
        if hasattr(request.user, 'institution'):
            institution = request.user.institution
        elif hasattr(request.user, 'institution_user'):
            inst_user = request.user.institution_user
            institution = inst_user.institution
        if not institution:
            messages.error(request, 'No institution associated with this user.')
            return redirect('login')  # Redirect if no institution found
        # Render institution dashboard with relevant data
        return render(request, 'certificates/institution_dashboard.html', {
            'institution': institution,
            'institution_user': inst_user,
            'certificate_types': institution.institution_type.allowed_certificate_types
        })
    elif request.user.user_type == 'student':
        # Student users see their own dashboard
        student = request.user.student
        certificates = Certificate.objects.filter(student=student)
        return render(request, 'certificates/student_dashboard.html', {
            'student': student,
            'certificates': certificates
        })
    else:
        messages.error(request, 'Invalid user type')
        return redirect('login')  # Redirect invalid users

@login_required
def institution_dashboard(request):
    # Specialized dashboard for institution users
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
    # Student dashboard showing student details and certificates
    student = request.user.student
    certificates = Certificate.objects.filter(student=student)
    context = {
        'student': student,
        'certificates': certificates
    }
    return render(request, 'certificates/student_dashboard.html', context)

@login_required
@user_passes_test(is_institution_user)  # Only institution users can issue certificates
def issue_certificate(request):
    # Determine institution from user or institution_user relation
    institution = getattr(request.user, 'institution', None)
    issuing_user = getattr(request.user, 'institution_user', None)
    if not institution and issuing_user:
        institution = issuing_user.institution
    if not institution:
        messages.error(request, "No institution associated with this user")
        return redirect('dashboard')

    from certificates.models import Student

    if request.method == 'POST':
        # Step 1: If the certificate issuance is confirmed
        if request.POST.get("confirmed") == "true":
            form = CertificateIssueForm(request.POST, institution=institution)
            if form.is_valid():
                student_identifier = form.cleaned_data['awardee_identifier']
                student = Student.objects.get(unique_identifier=student_identifier)
                try:
                    certificate_type = form.cleaned_data['certificate_type']
                    metadata = form.cleaned_data['metadata']
                    # Call service to issue certificate with provided data
                    certificate = issue_certificate_service(
                        institution=institution,
                        student=student,
                        certificate_type=certificate_type,
                        metadata=metadata,
                        issuing_user=issuing_user  # Important to track issuing user
                    )
                    messages.success(request, 'Certificate issued successfully')
                    return redirect('dashboard')
                except Exception as e:
                    messages.error(request, f'Error issuing certificate: {str(e)}')
            else:
                messages.error(request, "Invalid certificate data.")
        else:
            # Step 2: Show confirmation page before final issuance
            student_id = request.POST.get("awardee_identifier")
            student_name = ""
            try:
                student = Student.objects.get(unique_identifier=student_id)
                student_name = f"{student.firstname} {student.lastname}"
            except Student.DoesNotExist:
                pass  # If no student found, leave name blank

            metadata_raw = request.POST.get("metadata", "")
            try:
                metadata_obj = json.loads(metadata_raw)  # Parse metadata JSON
                metadata_json = json.dumps(metadata_obj, ensure_ascii=False)  # Pretty print JSON
            except Exception:
                metadata_json = metadata_raw  # Use raw string if JSON invalid

            # Prepare certificate info for confirmation template
            cert_info = {
                "type": request.POST.get("certificate_type"),
                "student_id": student_id,
                "student_name": student_name,
                "institution_name": institution.name,
                "metadata": metadata_json,
            }
            return render(request, 'certificates/confirm_certificate.html', {"cert_info": cert_info})

    # If GET or other methods, show empty issuance form
    form = CertificateIssueForm(institution=institution)
    return render(request, 'certificates/issue_certificate.html', {
        'form': form,
        'institution': institution
    })

@login_required
@user_passes_test(is_institution_user)  # Only institution users can review drafts
def review_draft(request, draft_id):
    if request.user.user_type != 'institution':
        raise PermissionDenied()  # Strictly restrict access to institutions

    user = request.user
    # Determine institution for the user, supporting both admin and department users
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution

    try:
        # Try to retrieve draft certificate belonging to institution
        draft = DraftCertificate.objects.get(
            id=draft_id,
            issuing_institution=institution
        )
        return render(request, 'certificates/review_draft.html', {
            'draft': draft
        })
    except DraftCertificate.DoesNotExist:
        messages.error(request, 'Draft certificate not found')
        return redirect('issue_certificate')  # Redirect if draft not found

@login_required
@user_passes_test(is_institution_user)  # Institution users can view institution certificates
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
        certificates = Certificate.objects.none()  # Empty queryset if no institution

    # Apply filters from GET params
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
        # Filter by student name or unique identifier (case-insensitive)
        certificates = certificates.filter(
            models.Q(student__firstname__icontains=search_query) |
            models.Q(student__lastname__icontains=search_query) |
            models.Q(student__unique_identifier__icontains=search_query)
        )

    certificate_types = Certificate.CERTIFICATE_TYPES  # All possible certificate types

    context = {
        'certificates': certificates.select_related('student', 'issuing_institution')
                                  .order_by('-created_at'),  # Order by latest
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
def certificate_details(request, certificate_hash):
    # Retrieve certificate with related student, institution, and issuing user
    cert = get_object_or_404(
        Certificate.objects.select_related('student', 'issuing_institution', 'issuing_user'),
        certificate_hash=certificate_hash
    )
    return render(request, 'certificates/certificate_details_modal.html', {
        'cert': cert
    })

@login_required
@user_passes_test(is_institution_user)
def confirm_certificate(request, draft_id):
    user = request.user
    # Determine institution for user
    institution = getattr(user, 'institution', None)
    if not institution and hasattr(user, 'institution_user'):
        institution = user.institution_user.institution

    if user.user_type != 'institution':
        raise PermissionDenied()  # Only institution users allowed

    if request.method != 'POST':
        return redirect('issue_certificate')  # Only POST allowed

    try:
        # Retrieve draft and confirm it to issue certificate
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
def db_verify_view(request):
    """
    POST: certificate_hash
    Returns JSON indicating if certificate exists in DB
    """
    if request.method == 'POST':
        cert_hash = request.POST.get('certificate_hash')
        # Check if certificate hash exists in DB
        exists = Certificate.objects.filter(certificate_hash=cert_hash).exists()
        return JsonResponse({'db_verified': exists})
    return JsonResponse({'db_verified': False})  # Return false if not POST

@login_required
def chain_verify_view(request):
    """
    POST: certificate_hash
    Returns JSON indicating if certificate is verified on blockchain
    """
    if request.method == 'POST':
        cert_hash = request.POST.get('certificate_hash')
        from certificates.services.verification import verify_certificate_full
        results = verify_certificate_full(cert_hash)
        # Return on-chain verification status
        return JsonResponse({'chain_verified': results['on_chain']})
    return JsonResponse({'chain_verified': False})

@login_required
def db_signature_verify_view(request):
    """
    POST: certificate_hash
    Returns JSON with DB existence and signature validity
    """
    if request.method == 'POST':
        cert_hash = request.POST.get('certificate_hash')
        result = verify_certificate_full(cert_hash)
        return JsonResponse({
            'db': result['db'],  # Certificate exists in DB
            'signature': result['signature'],  # Signature verification status
        })
    return JsonResponse({'db': False, 'signature': False})

@login_required
def full_verification_view(request):
    """
    POST: certificate_hash
    Returns JSON with full verification status: db, signature, on_chain
    """
    if request.method == 'POST':
        cert_hash = request.POST.get('certificate_hash')
        result = verify_certificate_full(cert_hash)
        return JsonResponse(result)  # Return full verification dictionary
    return JsonResponse({'db': False, 'signature': False, 'on_chain': False})

@login_required
@user_passes_test(is_institution_user)
def lookup_student(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            # Lookup student by unique identifier or linked user unique identifier
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
            # Return error if student not found
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            })
    # Invalid request method for lookup
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def logout_view(request):
    logout(request)  # Log out the current user
    return redirect('login')  # Redirect to login page after logout