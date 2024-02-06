from django.shortcuts import render, redirect
from django.contrib import messages
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database
from hmis.forms import PatientRegistrationForm

# Use the firebase_database object directly
db = firebase_database

def home(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = firebase_auth.sign_in_with_email_and_password(email, password)
            messages.success(request, 'Login successful!')
            # You can access user['idToken'] for Firebase user token if needed
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'hmis/home.html')

def dashboard(request):
    return render(request, 'hmis/dashboard.html')

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from the form
            cleaned_data = form.cleaned_data

            # Create user in Firebase Authentication
            email = cleaned_data['email']
            password = cleaned_data['password']
            try:
                user = firebase_auth.create_user_with_email_and_password(email, password)

                cleaned_data['birthday'] = str(cleaned_data['birthday'])

                # Save the form data to the database
                patient_data = {
                    'uid' :user['localId'],
                    'fname': cleaned_data['fname'],
                    'mname': cleaned_data['mname'],
                    'lname': cleaned_data['lname'],
                    'address': cleaned_data['address'],
                    'cnumber': cleaned_data['cnumber'],
                    'birthday': cleaned_data['birthday'],
                    'email': email,
                    'role': 'patient',  # You can add more fields as needed
                }
                db.child('patients').child(user['localId']).set(patient_data)

                messages.success(request, 'Registration successful! Please log in.')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = PatientRegistrationForm()

    return render(request, 'hmis/register.html', {'form': form})