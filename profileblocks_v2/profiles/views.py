# profiles/views.py

import io
import base64
import qrcode
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from certificates.models import Certificate
from .models import CertificateProfile
from profiles.services.profile_management import sign_profile
from django.conf import settings

# Helper function to check if user is authenticated student
def is_student_user(user):
    return user.is_authenticated and user.user_type == 'student'

@login_required
@user_passes_test(is_student_user)
def manage_profiles(request):
    # Get all certificate profiles for the logged-in student
    profiles = request.user.student.profiles.all()
    return render(request, 'profiles/manage_profiles.html', {'profiles': profiles})

@login_required
@user_passes_test(is_student_user)
def create_profile_select(request):
    # Retrieve all certificates belonging to the student
    certificates = Certificate.objects.filter(student=request.user.student)
    if request.method == "POST":
        # Get list of selected certificate IDs from POST data
        cert_ids = request.POST.getlist('cert_ids')
        if not cert_ids:
            messages.error(request, "Please select at least one certificate.")
            # Re-render selection page with error if none selected
            return render(request, 'profiles/create_profile_select.html', {'certificates': certificates})
        # Store selected certificate IDs in session for use in confirmation step
        request.session['profile_cert_ids'] = cert_ids
        return redirect('create_profile_confirm')
    # On GET, render certificate selection page
    return render(request, 'profiles/create_profile_select.html', {'certificates': certificates})

@login_required
@user_passes_test(is_student_user)
def create_profile_confirm(request):
    # Retrieve selected certificate IDs from session
    cert_ids = request.session.get('profile_cert_ids', [])
    # Query corresponding Certificate objects
    certificates = Certificate.objects.filter(id__in=cert_ids)
    if request.method == "POST":
        # Get profile name and optional description from form
        name = request.POST['name'].strip()
        description = request.POST.get('description', '').strip()
        student = request.user.student

        # Construct a JSON list of certificates with their hashes and signed hashes
        certs = [
            {
                "certificate_hash": cert.certificate_hash,
                "signed_hash": cert.signed_hash
            } for cert in certificates
        ]
        import json
        profile_json = json.dumps(certs, sort_keys=True)

        # Generate a signed profile ID by signing the JSON with student's private key
        profile_id = sign_profile(profile_json, student.private_key)
        signature = profile_id  # Use 15-char hash as signature/id

        # Create CertificateProfile object with generated ID and details
        profile = CertificateProfile.objects.create(
            id=profile_id,
            student=student,
            name=name,
            description=description,
            signed_profile_hash=signature
        )
        # Assign selected certificates to the profile
        profile.certificates.set(certificates)
        profile.save()
        # Mark the selected certificates as public now
        certificates.update(is_public=True)
        messages.success(request, "Profile created successfully and selected certificates are now public.")
        return redirect('certificate_profiles')
    # On GET, render confirmation page with selected certificates
    return render(request, 'profiles/create_profile_confirm.html', {'certificates': certificates})

@login_required
@user_passes_test(is_student_user)
def delete_profile(request, profile_id):
    # Fetch profile by ID ensuring it belongs to logged-in student
    profile = get_object_or_404(CertificateProfile, id=profile_id, student=request.user.student)
    if request.method == "POST":
        # Delete profile on POST and redirect with success message
        profile.delete()
        messages.success(request, "Profile deleted.")
        return redirect('certificate_profiles')
    # On GET, show confirmation page before deletion
    return render(request, 'profiles/delete_profile_confirm.html', {'profile': profile})

@login_required
def view_profile(request, profile_id):
    # Retrieve any profile by ID (no user check)
    profile = get_object_or_404(CertificateProfile, id=profile_id)
    return render(request, 'profiles/view_profile.html', {'profile': profile})

@login_required
@user_passes_test(is_student_user)
def export_profile_share(request, profile_id):
    # Get profile ensuring it belongs to the logged-in student
    profile = get_object_or_404(CertificateProfile, id=profile_id, student=request.user.student)
    signed_hash = profile.signed_profile_hash
    # Construct a shareable URL for profile verification
    share_url = f"http://{settings.HOST_URL}/profile_verification/{signed_hash}"

    # Generate a QR code for the share URL
    qr = qrcode.QRCode(
        version=1,  # QR code version (size)
        box_size=10,  # Size of each box in pixels
        border=5  # Border width in boxes
    )
    qr.add_data(share_url)  # Add the URL to the QR code
    qr.make(fit=True)       # Generate the QR code matrix
    img = qr.make_image(fill='black', back_color='white')  # Render QR code as image
    buffered = io.BytesIO()  # Buffer to hold image bytes
    img.save(buffered, format="PNG")  # Save image to buffer in PNG format
    img_str = base64.b64encode(buffered.getvalue()).decode()  # Convert to base64 string for embedding

    # Render export page with profile info, share URL, and QR code image encoded as base64
    return render(request, 'profiles/export_profile_share.html', {
        'profile': profile,
        'share_url': share_url,
        'qr_code_base64': img_str
    })