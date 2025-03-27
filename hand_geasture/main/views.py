from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
import json
from .models import *
from django.utils import timezone

def login_view(request):
    return render(request, 'login.html')


def logout_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    return render(request, 'logout.html')

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    return render(request, 'home.html')

def accounts_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    return render(request, 'accounts.html',{
        "users": UserProfiles.objects.all()
        })

def user_detail_view(request, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    user_profile = UserProfiles.objects.get(id=user_id)
    
    # Get all patients linked to this healthcare provider
    linked_patients = None
    if user_profile.role in ['doctor', 'nurse']:
        linked_patients = Patient.objects.filter(patient__account=user_profile)
    
    return render(request, 'user_detail.html', {
        'profile': user_profile,
        'linked_patients': linked_patients
    })

@require_POST
def login_ajax(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': 'Username and password are required'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has admin role
            try:
                user_profile = UserProfiles.objects.get(user=user)
                if user_profile.role != 'admin':
                    return JsonResponse({
                        'success': False,
                        'message': 'Access restricted to administrators only.'
                    }, status=403)
                
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect': '/'
                })
            except UserProfiles.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'User profile not found.'
                }, status=404)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials. Please try again.'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@require_POST
def create_account(request):
    try:
        data = json.loads(request.body)
        # Extract form data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        role = data.get('role')
        
        # Validate data
        if not all([username, password, email, first_name, last_name, role]):
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
        
        # Prevent admin account creation
        if role == 'admin':
            return JsonResponse({'success': False, 'message': 'Admin account creation is restricted'}, status=403)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile
        profile = UserProfiles.objects.create(
            user=user,
            role=role
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': profile.id,
                'username': user.username,
                'name': f"{user.first_name} {user.last_name}",
                'role': profile.role
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)


def patients_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    # Get all patients and order by alert status (True first, then False)
    # Using order_by('-alert') puts True values first since True > False
    patients = Patient.objects.all().order_by('-alert', 'name')
    return render(request, 'patients.html', {
        "patients": patients
    })

def patient_detail_view(request, patient_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = UserProfiles.objects.get(user=request.user)
        if user_profile.role != 'admin':
            return redirect('login')
    except UserProfiles.DoesNotExist:
        return redirect('login')
    
    patient = Patient.objects.get(id=patient_id)
    # Get all healthcare providers linked to this patient
    patient_links = PatientLink.objects.filter(patient=patient)
    
    return render(request, 'patient_detail.html', {
        'patient': patient,
        'patient_links': patient_links
    })

@require_POST
def update_profile(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        username = data.get('username')
        role = data.get('role')
        
        # Validate required fields
        if not all([user_id, first_name, last_name, email, username]):
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
        
        try:
            profile = UserProfiles.objects.get(id=user_id)
            user = profile.user
            
            # Check if username is being changed and already exists
            if username != user.username and User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)
            
            # Update user fields
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()
            
            # Prevent changing to admin role if user wasn't already admin
            if role == 'admin' and profile.role != 'admin':
                return JsonResponse({'success': False, 'message': 'Regular accounts cannot be elevated to Admin status'}, status=403)
            
            # Update role if user is not admin (for security)
            if profile.role != 'admin':
                profile.role = role
                profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'id': profile.id,
                    'username': user.username,
                    'name': f"{user.first_name} {user.last_name}",
                    'role': profile.role
                }
            })
            
        except UserProfiles.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User profile not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def delete_account(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        # Validate user_id
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID is required'}, status=400)
        
        try:
            profile = UserProfiles.objects.get(id=user_id)
            
            # Check if it's an admin account (security check)
            if profile.role == 'admin':
                return JsonResponse({
                    'success': False, 
                    'message': 'Admin accounts cannot be deleted for security reasons'
                }, status=403)
            
            # Delete the user (will also delete profile through CASCADE)
            user = profile.user
            username = user.username
            user.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Account {username} has been deleted successfully',
                'redirect': '/accounts/'
            })
            
        except UserProfiles.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User profile not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def reset_password(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        # Validate required fields
        if not all([user_id, new_password]):
            return JsonResponse({'success': False, 'message': 'User ID and new password are required'}, status=400)
        
        try:
            profile = UserProfiles.objects.get(id=user_id)
            user = profile.user
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Update password last changed date
            profile.password_last_changed = timezone.now()
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Password reset successfully',
                'last_changed': profile.password_last_changed.strftime('%B %d, %Y')
            })
            
        except UserProfiles.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User profile not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def create_patient(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        age = data.get('age')
        password = data.get('password')
        alert = data.get('alert', False)
        
        # Validate data
        if not all([name, age, password]):
            return JsonResponse({'success': False, 'message': 'Name, age, and password are required'}, status=400)
        
        # Create patient
        patient = Patient.objects.create(
            name=name,
            age=age,
            password=password,  # In a real app, this should be hashed
            alert=alert
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Patient added successfully',
            'patient': {
                'id': patient.id,
                'name': patient.name,
                'age': patient.age,
                'alert': patient.alert
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def get_available_providers(request):
    try:
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'message': 'Patient ID is required'}, status=400)
        
        # Get patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=404)
        
        # Get currently linked provider IDs
        linked_provider_ids = PatientLink.objects.filter(patient=patient).values_list('account_id', flat=True)
        
        # Get all providers that are not already linked to this patient and are not admins
        available_providers = UserProfiles.objects.exclude(id__in=linked_provider_ids).exclude(role='admin')
        
        providers_data = []
        for provider in available_providers:
            providers_data.append({
                'id': provider.id,
                'name': f"{provider.user.first_name} {provider.user.last_name}",
                'role': provider.role
            })
        
        return JsonResponse({
            'success': True,
            'providers': providers_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def link_provider(request):
    try:
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        provider_id = data.get('provider_id')
        
        if not all([patient_id, provider_id]):
            return JsonResponse({'success': False, 'message': 'Patient ID and Provider ID are required'}, status=400)
        
        # Get patient and provider
        try:
            patient = Patient.objects.get(id=patient_id)
            provider = UserProfiles.objects.get(id=provider_id)
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=404)
        except UserProfiles.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Provider not found'}, status=404)
        
        # Check if link already existsadmin (security check)
        if PatientLink.objects.filter(patient=patient, account=provider).exists():
            return JsonResponse({'success': False, 'message': 'Provider is already linked to this patient'}, status=400)
        
        # Check if link already exists
        if PatientLink.objects.filter(patient=patient, account=provider).exists():
            return JsonResponse({'success': False, 'message': 'Provider is already linked to this patient'}, status=400)
        
        # Create the link
        PatientLink.objects.create(patient=patient, account=provider)
        
        return JsonResponse({
            'success': True,
            'message': 'Provider linked successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def unlink_provider(request):
    try:
        data = json.loads(request.body)
        link_id = data.get('link_id')
        
        if not link_id:
            return JsonResponse({'success': False, 'message': 'Link ID is required'}, status=400)
        
        # Get link
        try:
            link = PatientLink.objects.get(id=link_id)
        except PatientLink.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Link not found'}, status=404)
        
        # Delete the link
        link.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Provider unlinked successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def update_patient(request):
    try:
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        name = data.get('name')
        age = data.get('age')
        alert = data.get('alert', False)
        password = data.get('password', None)
        
        # Validate required fields
        if not all([patient_id, name, age]):
            return JsonResponse({'success': False, 'message': 'Patient ID, name, and age are required'}, status=400)
        
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Update patient fields
            patient.name = name
            patient.age = age
            patient.alert = alert
            if password:  # Only update password if provided
                patient.password = password  # In a real app, this should be hashed
            
            patient.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Patient updated successfully',
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'age': patient.age,
                    'alert': patient.alert
                }
            })
            
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

@require_POST
def delete_patient(request):
    try:
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'success': False, 'message': 'Patient ID is required'}, status=400)
        
        try:
            patient = Patient.objects.get(id=patient_id)
            patient_name = patient.name
            
            # Delete the patient (will also delete patient links through CASCADE)
            patient.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Patient {patient_name} has been deleted successfully'
            })
            
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    

# ------------------Patient------------------

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password

@csrf_exempt
def patient_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        name = data.get("name")
        password = data.get("password")

        try:
            patient = Patient.objects.get(name=name)
            if password == patient.password:
                request.session["patient_id"] = patient.id
                return JsonResponse({"message": "Login successful", "status": "success", "session_id": request.session.session_key})
            else:
                return JsonResponse({"message": "Invalid password", "status": "error"}, status=401)
        except Patient.DoesNotExist:
            return JsonResponse({"message": "Patient not found", "status": "error"}, status=404)

    return JsonResponse({"message": "Only POST method allowed"}, status=405)

@csrf_exempt
def get_patient_details(request):
    if request.method == "GET":
        patient_id = request.session.get("patient_id")
        if not patient_id:
            return JsonResponse({"message": "Unauthorized", "status": "error"}, status=401)
        try:
            patient = Patient.objects.get(id=patient_id)
            return JsonResponse({
                "name": patient.name,
                "age": patient.age,
                "alert": patient.alert
            })
        except Patient.DoesNotExist:
            return JsonResponse({"message": "Patient not found", "status": "error"}, status=404)

    return JsonResponse({"message": "Only GET method allowed"}, status=405)

@csrf_exempt
def patient_alert_yes(request):
    if request.method == "POST":
        patient_id = request.session.get("patient_id")
        if not patient_id:
            return JsonResponse({"message": "Unauthorized", "status": "error"}, status=401)
        try:
            patient = Patient.objects.get(id=patient_id)
            patient.alert = True
            patient.save()
            return JsonResponse({"message": "Alert status updated", "status": "success"})
        except Patient.DoesNotExist:
            return JsonResponse({"message": "Patient not found", "status": "error"}, status=404)

    return JsonResponse({"message": "Only POST method allowed"}, status=405)

@csrf_exempt
def patient_alert_no(request):
    if request.method == "POST":
        patient_id = request.session.get("patient_id")
        if not patient_id:
            return JsonResponse({"message": "Unauthorized", "status": "error"}, status=401)
        try:
            patient = Patient.objects.get(id=patient_id)
            patient.alert = False
            patient.save()
            return JsonResponse({"message": "Alert status updated", "status": "success"})
        except Patient.DoesNotExist:
            return JsonResponse({"message": "Patient not found", "status": "error"}, status=404)

    return JsonResponse({"message": "Only POST method allowed"}, status=405)

# ------------------Doctor------------------

