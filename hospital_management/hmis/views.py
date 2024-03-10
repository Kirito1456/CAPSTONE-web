from django.shortcuts import render, redirect
from django.contrib import messages
from hmis.models import Medications
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database
from hmis.forms import StaffRegistrationForm, MedicationsListForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage

 
from PIL import Image 
from pytesseract import pytesseract 

import uuid
import json
from .database import connect_to_mongodb

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
            return redirect('patient_data_doctor_view')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'hmis/home.html')

def dashboard(request):
    # Fetch doctors and nurses data from Firebase
    doctors = db.child("doctors").get().val()
    nurses = db.child("nurses").get().val()

    # Combine doctors and nurses data into one dictionary
    accounts = {}
    if doctors:
        accounts.update(doctors)
    if nurses:
        accounts.update(nurses)

    # Pass the combined data to the template
    return render(request, 'hmis/dashboard.html', {'accounts': accounts})


def register(request):
    return render(request, 'hmis/register.html')

def create(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            email = cleaned_data['email']
            password = cleaned_data['password']
            confirmpassword = cleaned_data['confirmpassword']

            # Check if passwords match
            if password != confirmpassword:
                messages.error(request, 'Passwords do not match.')
                return redirect('create')

            # Validate password strength
            try:
                validate_password(password)
            except ValidationError as e:
                messages.error(request, 'Password is too weak.')
                return redirect('create')

            # Check if email is already used
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already used.')
                return redirect('create')

            try:
                # Create user in Firebase Authentication
                user = firebase_auth.create_user_with_email_and_password(email, password)

                # Convert birthday to string or format it appropriately
                cleaned_data['birthday'] = str(cleaned_data['birthday'])

                data = {
                    'uid': user['localId'],
                    'fname': cleaned_data['fname'],
                    'lname': cleaned_data['lname'],
                    'cnumber': cleaned_data['cnumber'],
                    'birthday': cleaned_data['birthday'],
                    'sex': cleaned_data['sex'],
                    'role': cleaned_data['role'],
                    'jobTitle': cleaned_data['jobTitle'],
                    'department': cleaned_data['department'],
                    'email': email,
                }

                # Save the form data to the database
                # db.child('staff').child(user['localId']).set(data)

                if (cleaned_data['role'] == 'Doctor'):
                    db.child('doctors').child(user['localId']).set(data)
                else:
                    db.child('nurses').child(user['localId']).set(data)

                messages.success(request, 'Registration successful! Please log in.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = StaffRegistrationForm()

    return render(request, 'hmis/register.html', {'form': form})

def forgotpass(request):
    return render(request, 'hmis/forgotpass.html')
 
def reset(request):
    if request.method == 'POST':
        # Get the email from the form data
        email = request.POST.get('email-fp')
        try:
            # Send password reset email using Firebase Authentication
            firebase_auth.send_password_reset_email(email)
            message = "An email to reset your password has been successfully sent."
            # Display success message to the user
            return render(request, 'hmis/forgotpass.html', {"msg": message})
        except:
            # Handle any exceptions, such as invalid email or network issues
            message = "Something went wrong. Please make sure the email you provided is registered."
            # Display error message to the user
            return render(request, 'hmis/forgotpass.html', {"msg": message})
    # If the request method is not POST, render the forgot password form
    else:
        return render(request, 'hmis/forgotpass.html')



def patient_data_doctor_view(request):
    # Fetch patients from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()

    # Pass the patients data to the template
    return render(request, 'hmis/patient_data_doctor_view.html', {'patients': patients, 'patientsdata': patientsdata})

def patient_personal_information(request):
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()

    chosenPatient = request.GET.get('chosenPatient', '')

    chosenPatientData = {}
    for patients_id, patients_data in patients.items():
        if chosenPatient == patients_data["uid"]:
            chosenPatientData[patients_id] = patients_data

            #retrieve patient birthdate
            chosenPatientBirthday = chosenPatientData[chosenPatient].get("bday")
            #calculate patient age function
            chosenPatientAge = calculate_age(chosenPatientBirthday)

    chosenPatientDatas = {}
    for patientsdata_id, patientsdata_data in patientsdata.items():
        if chosenPatient == patientsdata_data["patientid"]:
            chosenPatientDatas[patientsdata_id] = patientsdata_data

    return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 'chosenPatientDatas': chosenPatientDatas, 'chosenPatientAge' : chosenPatientAge})

#Calculate age function for retrieving patient data
from datetime import datetime
def calculate_age(birthday):
    today = datetime.today()
    print(today)
    birthdate = datetime.strptime(birthday, '%Y-%m-%d').date()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def new_vital_sign_entry(request):
    return render(request, 'hmis/new_vital_sign_entry.html')

def patient_medical_history(request):
    return render(request, 'hmis/patient_medical_history.html')

def view_treatment_plan(request):
    return render(request, 'hmis/view_treatment_plan.html')

def view_treatment_plan(request, fname, lname, gender, bday):
    return render(request, 'hmis/view_treatment_plan.html', {'fname': fname, 'lname': lname, 'gender': gender, 'bday': bday})

def patient_medication_doctor(request):
    # Fetch patients data from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()

    # Pass the combined data to the template
    return render(request, 'hmis/patient_medication_doctor.html', {'patients': patients, 'patientsdata': patientsdata})


def patient_medication_nurse(request):
    return render(request, 'hmis/patient_medication_nurse.html')

def patient_medication_table(request):
    return render(request, 'hmis/patient_medication_table.html')

def patient_medication_table(request, fname, lname, gender, bday):
    return render(request, 'hmis/patient_medication_table.html', {'fname': fname, 'lname': lname, 'gender': gender, 'bday': bday})

def inpatient_medication_order(request):
    return render(request, 'hmis/inpatient_medication_order.html')

def perform_ocr(request):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        img = Image.open(uploaded_image)
        text = pytesseract.image_to_string(img)
        return HttpResponse(text)
    
    # Return a bad request response if no image is uploaded or if request method is not POST
    return HttpResponse('No image uploaded or invalid request.')

def pharmacy_drugs(request):
    collection = connect_to_mongodb()
    cursor = collection.find().limit(10)

    # Convert the cursor to a list of dictionaries
    data = list(cursor)
    print(data)

    # Pass the data to the template for rendering
    return render(request, 'hmis/test.html', {'data': data})

def generate_unique_id():
    return str(uuid.uuid4())

def outpatient_medication_order(request):
    patients = db.child("patients").get().val()
    collection = connect_to_mongodb()
    medications_cursor = collection.find({}, {"Generic Name": 1, "_id": 0})
    medicines_list = [medication['Generic Name'] for medication in medications_cursor]

    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 'medicines_list': medicines_list})

def diagnostic_lab_reports(request):
    return render(request, 'hmis/diagnostic_lab_reports.html')

def diagnostic_imagery_reports(request):
    return render(request, 'hmis/diagnostic_imagery_reports.html')

def patient_personal_information_inpatient(request):
    return render(request, 'hmis/patient_personal_information_inpatient.html')