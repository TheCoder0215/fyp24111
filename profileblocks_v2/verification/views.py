from django.shortcuts import render, get_object_or_404
from profiles.models import CertificateProfile
from certificates.models import Certificate
from certificates.services.verification import verify_certificate_full
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def public_certificate_verification(request):
    cert = None  # Initialize cert variable to None
    result = None  # Initialize verification result to None
    cert_hash = ""  # Initialize certificate hash as empty string
    # Handle GET request with a 'hash' parameter
    if request.method == "GET" and request.GET.get("hash"):
        cert_hash = request.GET.get("hash")  # Retrieve the certificate hash from query params
        try:
            # Try to get the Certificate object with related issuing_institution, issuing_user, and student
            cert = Certificate.objects.select_related('issuing_institution', 'issuing_user', 'student').get(certificate_hash=cert_hash)
            result = verify_certificate_full(cert_hash)  # Verify certificate by hash
        except Certificate.DoesNotExist:
            # If certificate not found, set cert and result to None
            cert = None
            result = None
    # Render the public verification template with cert, result, and cert_hash context variables
    return render(request, "verification/public_certificate_verification.html", {
        "cert": cert,
        "result": result,
        "cert_hash": cert_hash
    })

@csrf_exempt  # Disable CSRF protection for this view
def public_db_signature_verify(request):
    # Only handle POST requests
    if request.method == "POST":
        cert_hash = request.POST.get("certificate_hash")  # Get certificate hash from POST data
        result = verify_certificate_full(cert_hash)  # Verify certificate
        # Return a JSON response containing db and signature verification results
        return JsonResponse({
            "db": result["db"],
            "signature": result["signature"]
        })
    # If not POST, return JSON with False values
    return JsonResponse({"db": False, "signature": False})

@csrf_exempt  # Disable CSRF protection for this view
def public_full_verification(request):
    # Handle POST requests only
    if request.method == "POST":
        cert_hash = request.POST.get("certificate_hash")  # Extract certificate hash from POST data
        result = verify_certificate_full(cert_hash)  # Perform full verification
        return JsonResponse(result)  # Return full result as JSON response
    # Return default failure response if not POST
    return JsonResponse({"db": False, "signature": False, "on_chain": False})

def landing(request):
    # Render a simple landing page template
    return render(request, 'verification/landing.html')

def verify_profile(request, signed_hash):
    # Retrieve CertificateProfile object or return 404 if not found
    profile = get_object_or_404(CertificateProfile, signed_profile_hash=signed_hash)
    # Get all certificates related to this profile
    certificates = profile.certificates.all()
    # Render template to verify profile, passing profile info and certificates
    return render(request, 'verification/verify_profile.html', {
        'profile': profile,
        'certificates': certificates,
        'verified': True,  # Flag indicating profile is verified
    })