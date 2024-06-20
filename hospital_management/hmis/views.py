from datetime import datetime , timedelta
import datetime as date
import re
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database, storage as firebase_storage
from hmis.forms import StaffRegistrationForm, AppointmentScheduleForm, MedicationsListForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import logout as auth_logout
from django.core.mail import send_mail
import json
import uuid
import random

from hmis.models import Medications
from hospital_management.settings import collection 
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage

from PIL import Image 
from pytesseract import pytesseract 

import uuid
import json
# from hmis.OCR import recognise 

from django.http import HttpResponse, JsonResponse
from PIL import Image
import pytesseract
import base64
from firebase_admin import db

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# Use the firebase_database object directly
db = firebase_database

# views.py
import firebase_admin
from firebase_admin import storage
from django.shortcuts import render, redirect
from .forms import ImageUploadForm

from django.shortcuts import render
from django.http import JsonResponse
from paddleocr import PaddleOCR

import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            # Upload image to Firebase Storage
            bucket = storage.bucket("your-firebase-storage-bucket-url")
            blob = bucket.blob(image.name)
            blob.upload_from_string(image.read(), content_type=image.content_type)
            # Get the URL of the uploaded image
            image_url = blob.public_url
            return redirect('success_url')  # Redirect to a success page
    else:
        form = ImageUploadForm()
    return render(request, 'hmis/upload_image.html', {'form': form})


def home(request):
    storage = messages.get_messages(request)
    storage.used = True
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = firebase_auth.sign_in_with_email_and_password(email, password)
            session_id = user['localId']
            request.session['uid'] = str(session_id)
            # print(request.session['uid'])

            #db.child('sessions').child(user['localId']).set(user)

            # subject = 'Welcome to My Site'
            # message = 'Thank you for creating an account!'
            # from_email = 'jmmojica0701@gmail.com'
            recipient_list = [email]
            # send_mail(subject, message, from_email, recipient_list)
            
            # send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, 'Login successful!')

            # Fetch doctors and nurses data from Firebase
            doctors = db.child("doctors").get().val()
            nurses = db.child("nurses").get().val()

            # Combine doctors and nurses data into one dictionary
            accounts = {}
            if doctors:
                accounts.update(doctors)
            if nurses:
                accounts.update(nurses)

            # You can access user['idToken'] for Firebase user token if needed
            if email == "admin@gmail.com":
                return redirect('clinics')
            
            doctor_found = False
            nurse_found = False
            chargenurse_found = False
            for account in accounts.values():
                if account["role"] == "Doctor" and account["email"] == email:
                    doctor_found = True
                elif account["role"] == "Nurse" and account["email"] == email:
                    nurse_found = True
                    if account["specialization"] == "Charge Nurse" and account["email"] == email:
                        chargenurse_found = True
                    break

            if doctor_found:
                return redirect('DoctorDashboard')
            elif nurse_found and chargenurse_found:
                return redirect('ChargeNurseDashboard')
            elif nurse_found and chargenurse_found == False:
                return redirect('NurseDashboard')
            else:
                return redirect('register')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'hmis/home.html')

def dashboard(request):

    if request.method == 'POST':
        # Get the clinic ID from the form data
        clinic_id = request.POST.get('staff')

        # Fetch all doctors and nurses data from Firebase
        all_doctors = db.child("doctors").get().val()
        all_nurses = db.child("nurses").get().val()

        # Initialize an empty dictionary to store filtered accounts
        accounts = {}

        # Filter doctors by clinic ID and add to accounts
        if all_doctors:
            for doctor_id, doctor_data in all_doctors.items():
                if doctor_data.get("clinic") == clinic_id:
                    accounts[doctor_id] = doctor_data

        # Filter nurses by clinic ID and add to accounts
        if all_nurses:
            for nurse_id, nurse_data in all_nurses.items():
                if nurse_data.get("clinic") == clinic_id:
                    accounts[nurse_id] = nurse_data

        # Pass the filtered data to the template
        return render(request, 'hmis/dashboard.html', {'accounts': accounts})
    else:
        # Handle GET request or other cases where no POST data is available
        return render(request, 'hmis/dashboard.html', {})




def clinics(request):
    # Fetch doctors and nurses data from Firebase
    clinics = db.child("clinics").get().val()

    # Combine doctors and nurses data into one dictionary
    accounts = {}
    if clinics:
        accounts.update(clinics)

    # Pass the combined data to the template
    return render(request, 'hmis/clinics.html', {'accounts': accounts})

def nursesAdmin(request):
    # Fetch doctors and nurses data from Firebase
    nurses = db.child("nurses").get().val()

    if request.method == 'POST':
        try:
            for nurse_id in request.POST.getlist('nurseID'):
                shift = request.POST.get(f'shift_{nurse_id}')  
                data = {
                    'shift': shift
                }
                db.child('nurses').child(nurse_id).update(data)

                messages.success(request, 'Nurse Assignments saved successfully!')
            return redirect('nursesAdmin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')


    # Pass the combined data to the template
    return render(request, 'hmis/nurses.html', {'nurses': nurses})


def register(request):
    
    clinics = db.child("clinics").get().val()

    # Combine doctors and nurses data into one dictionary
    accounts = {}
    if clinics:
        accounts.update(clinics)
    
    return render(request, 'hmis/register.html', {'accounts': accounts})

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
                return redirect('register')

            # Validate password strength
            try:
                validate_password(password)
            except ValidationError as e:
                messages.error(request, 'Password is too weak.')
                return redirect('register')

            # Check if email is already used
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already used.')
                return redirect('register')

            try:
                clinic = request.POST.get('clinic')
                
                # Check if clinic data is provided
                id = str(uuid.uuid1())
                clinic_data = {
                    'name': request.POST.get('newclinic'),
                    'fnumber': request.POST.get('fnumber'),
                    'onumber': request.POST.get('onumber'),
                    'rnumber': request.POST.get('rnumber'),
                    'uid': id
                }

                #print(clinic_data)

                if clinic_data['name']:
                    # Save new clinic data
                    clinic_ref =  db.child('clinics').child(id).set(clinic_data)
                    #clinic_id = clinic_ref.key  # Get the unique key of the pushed clinic
                    clinic = id

                # Create user in Firebase Authentication
                user = firebase_auth.create_user_with_email_and_password(email, password)

                
                data = {
                    'uid': user['localId'],
                    'fname': cleaned_data['fname'],
                    'lname': cleaned_data['lname'],
                    'sex': cleaned_data['sex'],
                    'role': cleaned_data['role'],
                    'specialization': cleaned_data['specialization'],
                    #'department': cleaned_data['department'],
                    'clinic': clinic,
                    'email': email,
                }

                data2 = {
                    'uid': user['localId'],
                    'fname': cleaned_data['fname'],
                    'lname': cleaned_data['lname'],
                    'sex': cleaned_data['sex'],
                    'role': cleaned_data['role'],
                    'specialization': cleaned_data['specialization'],
                    'shift': '',
                    #'department': cleaned_data['department'],
                    #'clinic': clinic,
                    'email': email,
                }


                if (cleaned_data['role'] == 'Doctor'):
                    db.child('doctors').child(user['localId']).set(data)
                else:
                    db.child('nurses').child(user['localId']).set(data2)
                               
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('home')
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


def logout(request):
    #auth_logout(request)
    #request.session.flush()
    storage = messages.get_messages(request)
    storage.used = True
    try:
        del request.session['uid']
        messages.success(request, 'Logged out successfully.')
    except KeyError:
        pass
    
    #firebase_auth.signOut()
    return redirect('home')

def profile(request):
    # Fetch doctors and nurses data from Firebase
    doctors = db.child("doctors").get().val()
    nurses = db.child("nurses").get().val()
    uid = request.session['uid'] 

            # Combine doctors and nurses data into one dictionary
    accounts = {}
    if doctors:
        accounts.update(doctors)
    if nurses:
        accounts.update(nurses)
    
    return render(request, 'hmis/Profile.html', {'uid': uid, 'accounts': accounts})

def update_profile (request):
    if request.method == 'POST':
        try:
            uid = request.POST.get('update')
            onumber = request.POST.get('cnumber')
            department = request.POST.get('department')
            role = request.POST.get('rselected')
            clinicname = request.POST.get('clinicname')
            clinicaddress = request.POST.get('clinicaddress')
            #print(uid)
            #print(role)

            db_path = ""

            # Construct the path to the appointment data in Firebase
            if role == 'Doctor':
                db_path = f"/doctors/{uid}"
            elif role == 'Nurse':
                db_path = f"/nurses/{uid}"  # Adjust the path as per your Firebase structure

            # Update appointment data in Firebase
            db.child(db_path).update({
                'cnumber': onumber,
                'department': department,
                'clinicname': clinicname,
                'clinicaddress': clinicaddress
            }) 

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('Profile')  # Redirect to the appointments list page

    # Handle GET request or invalid form submission
    return redirect('Profile')

# Function to get upcoming appointments
def AppointmentUpcoming(request):
    
    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']    

    next_available_dates = []
    time_slots = []
    days_checked = 0

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    if upcomings:
        for appointment_id, appointment_data in upcomings.items():
            if appointment_data["doctorUID"] == uid:
                appointment_date_str = appointment_data.get("appointmentDate", "")
                appointment_time_str = appointment_data.get("appointmentTime", "")
            
                if appointment_date_str and appointment_time_str:
                    # Convert appointment date string to datetime object
                    appointment_datetime = date.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
                
                    # Check if appointment date is in the future
                    if appointment_datetime >= date.datetime.now() and appointment_data["status"] == "Ongoing":
                        upcoming_appointments[appointment_id] = appointment_data

        # Sort appointments by date
        sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_upcoming_appointments = {}

    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
    if appointmentschedule_data:
        available_days_str = appointmentschedule_data.get("days", "")
        day_name_to_number = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }

        available_days_numbers = [day_name_to_number[day.lower()] for day in available_days_str if day.lower() in day_name_to_number]
        
        current_day_of_week = datetime.now().weekday()
        current_date = datetime.now()
        next_available_date = None  # Initialize the variable to store the next available date
        while days_checked < 7:  # Check up to 7 days
            if current_day_of_week in available_days_numbers:
                if current_date.date():
                    next_available_date = current_date.date()
                    break  # Exit the loop as soon as the first available date is found
            current_date += timedelta(days=1)
            current_day_of_week = (current_day_of_week + 1) % 7
            days_checked += 1

        next_available_date_str = next_available_date.strftime('%Y-%m-%d')

        appointments_for_specific_date = [appointment_data for appointment_data in upcoming_appointments.values() if appointment_data['appointmentDate'] == next_available_date_str]
        booked_time_slots = set(appointment['appointmentTime'] for appointment in appointments_for_specific_date)
       
        # Define the start and end time for morning and afternoon appointments for the specific date
        morning_start = datetime.strptime(appointmentschedule_data.get("morning_start"), '%H:%M')
        morning_end = datetime.strptime(appointmentschedule_data.get("morning_end"), '%H:%M')
        afternoon_start = datetime.strptime(appointmentschedule_data.get("afternoon_start"), '%H:%M')
        afternoon_end = datetime.strptime(appointmentschedule_data.get("afternoon_end"), '%H:%M')
        
        interval = timedelta(minutes=30)
        
        # Calculate time slots for morning
        current_time = morning_start
        while current_time <= morning_end:
            # Check if the current time slot is not booked
            if current_time.strftime('%I:%M %p') not in booked_time_slots:
                time_slots.append(current_time.strftime('%I:%M %p'))  # Include AM/PM
            current_time += interval

        # Calculate time slots for afternoon
        current_time = afternoon_start
        while current_time <= afternoon_end:
            # Check if the current time slot is not booked
            if current_time.strftime('%I:%M %p') not in booked_time_slots:
                time_slots.append(current_time.strftime('%I:%M %p'))  # Include AM/PM
            current_time += interval
    else: 
        next_available_date_str = ''
            
    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentUpcoming.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors, 'time_slots': time_slots,
                                                             'next_available_date_str': next_available_date_str, 'time_slots': time_slots})
def update_appointment(request):
    
    if request.method == 'POST':
        try:
            appID = request.POST.get('appID')

            new_time = request.POST.get('new_appointment_time')
            new_date = request.POST.get('selected_appointment_date')
            
            data = {
                'appointmentDate': new_date,
                'appointmentTime': new_time,
                'status': 'Ongoing',
            }
            db.child('appointments').child(appID).update(data)

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('AppointmentUpcoming')  # Redirect to the appointments list page

    # Handle GET request or invalid form submission
    return redirect('AppointmentUpcoming')

def delete_appointment(request):
    if request.method == 'POST':
        try:
            # Get the appointment ID from the form data
            appointment_id = request.POST.get('cancel')

            # Construct the path to the data you want to delete
            path_to_data = f"/appointments/{appointment_id}"  # Adjust the path as per your Firebase structure

            # Use the reference to access the data and delete it
            db.child(path_to_data).remove()

            messages.success(request, 'Appointment canceled successfully')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('AppointmentUpcoming')  # Redirect to the appointments list page

    # Render a template if the request method is not POST
    return render(request, 'hmis/AppointmentUpcoming.html')

def followup_appointment(request):
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    # appointment_id = request.GET.get('appointmentID', '')
    appointmentschedule = db.child("appointmentschedule").get().val()
    # print('appointment_id is ', appointment_id)
    
    if request.method == 'POST':
        endAppointmentPatientID = request.POST.get('followupCheckbox')
        endAppointmentAPP = request.POST.get('endAppointment')
        # print('endAppointmentAPP IS ', endAppointmentAPP)
        if endAppointmentPatientID:
            id=str(uuid.uuid1())
            endAppointment = request.POST.get('past-appointment-id')
        
            new_time = request.POST.get('new_appointment_time1')
            new_date = request.POST.get('selected_appointment_date1')
            # print('new_time is ', new_time)
            # print('new_date is ', new_date)
            data = {
                'appointmentDate': new_date,
                'appointmentTime': new_time,
                'status': 'Ongoing',
                'doctorUID': uid,
                'appointmentVisitType': "Follow-Up Visit",
                'patientName': endAppointmentPatientID
            }
            db.child("appointments").child(id).set(data)

        db.child("appointments").child(endAppointmentAPP).update({'status': 'Finished'})

        return redirect('DoctorDashboard')  # Redirect to the appointments list page

    return render(request, 'hmis/AppointmentUpcoming.html', {'uid': uid,
                                                            'appointmentschedule': appointmentschedule,})
        

def AppointmentPast(request):

    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    pasts = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    consulNotes = db.child("consultationNotes").get().val()
    uid = request.session['uid']

    # Filter and sort upcoming appointments
    past_appointments = {}
    notes = {}
    if pasts:
        for appointment_id, appointment_data in pasts.items():
            if appointment_data["doctorUID"] == uid:
                appointment_date_str = appointment_data.get("appointmentDate", "")
                appointment_time_str = appointment_data.get("appointmentTime", "")
            
                if appointment_date_str and appointment_time_str:
                # Convert appointment date string to datetime object
                    appointment_datetime = date.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
                
                # Check if appointment date is in the future
                    if appointment_datetime < date.datetime.now() or appointment_data["status"] == "Finished":
                        past_appointments[appointment_id] = appointment_data

        # Sort appointments by date
        sorted_past_appointments = dict(sorted(past_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_past_appointments = {}
    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentPast.html', {'appointments': sorted_past_appointments, 'patients': patients,
                                                         'uid': uid, 'doctors': doctors})
    
def AppointmentCalendar(request):
    
    if request.session.get('uid') is None:
        return redirect('home')
    
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']

    id = request.session.get('uid')
    patients = db.child("patients").get().val()
    appointments = db.child("appointments").get().val()

    task = []
    if appointments:
        for appointment_id, appointment_data in appointments.items():
            if appointment_data.get('doctorUID') == id:
                hdate = appointment_data.get('appointmentDate')
                appointment_time = appointment_data.get('appointmentTime')
                patient_uid = appointment_data.get('patientName')
            
                for patient_id, patient_data in patients.items():
                    if patient_uid == patient_id:
                        patient_name = patient_data.get('fname') +  ' ' + patient_data.get('lname')
                        task_item = {'hdate': hdate, 'task':f"{appointment_time} {patient_name}"}
                        task.append(task_item)

        task_json = json.dumps(task)
    else:
        task_json = ''
    
    return render(request, 'hmis/AppointmentCalendar.html', {'uid': uid, 'doctors': doctors, 'task_json': task_json})

def AppointmentScheduling(request):
    doctors = db.child("doctors").get().val()
    uid = request.session.get('uid')
    schedule = db.child("appointmentschedule").get().val()

    if request.method == 'POST':
        selected_days = request.POST.getlist('selected_days')  # Get list of selected days
        morning_start = request.POST.get('morning_start')
        morning_end = request.POST.get('morning_end')
        afternoon_start = request.POST.get('afternoon_start')
        afternoon_end = request.POST.get('afternoon_end')

        try:
            if not isinstance(selected_days, list):
                selected_days = [selected_days]

            # Save appointment schedule to Firebase
            data = {
                'uid': uid,
                'days': selected_days,
                'morning_start': str(morning_start),
                'morning_end': str(morning_end),
                'afternoon_start': str(afternoon_start),
                'afternoon_end': str(afternoon_end),
            }
            db.child('appointmentschedule').child(uid).set(data)

            messages.success(request, 'Appointment schedule saved successfully!')
            return redirect('AppointmentScheduling')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    else:
        # Retrieve appointment schedule data from Firebase
        appointment_schedule = db.child('appointmentschedule').child(uid).get().val()
        if appointment_schedule:
            selected_days = appointment_schedule.get('days', [])
            morning_start = appointment_schedule.get('morning_start', '')
            morning_end = appointment_schedule.get('morning_end', '')
            afternoon_start = appointment_schedule.get('afternoon_start', '')
            afternoon_end = appointment_schedule.get('afternoon_end', '')
        else:
            # Set default values if no appointment schedule found
            selected_days = []
            morning_start = ''
            morning_end = ''
            afternoon_start = ''
            afternoon_end = ''

    return render(request, 'hmis/AppointmentScheduling.html', {'uid': uid, 'doctors': doctors, 'selected_days': selected_days, 'morning_start': morning_start, 'morning_end': morning_end, 'afternoon_start': afternoon_start, 'afternoon_end': afternoon_end})
def NurseDashboard(request):
    nurses = db.child("nurses").get().val()
    uid = request.session['uid'] 
    patients = db.child("patients").get().val()

    # for patient_id, patient_data in patients.items():
    #     patient_data['room_number'] = random.randint(100, 999)

    # context = {
    #     'patients': patients,
    # }

    return render(request, 'hmis/nursedashboard.html', {'nurses': nurses, 'uid': uid, 'patients': patients})

def DoctorDashboard(request):
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    patientdatas = db.child("patientdata").get().val()
    patientsdata = db.child("patientdata").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    rooms = db.child("rooms").get().val()
    submittedTest = db.child("submittedTest").get().val()
    appointments = db.child("appointments").get().val()

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    inpatients = {}
    if upcomings:
        for appointment_id, appointment_data in upcomings.items():
            if appointment_data["doctorUID"] == uid:
                appointment_date_str = appointment_data.get("appointmentDate", "")
                appointment_time_str = appointment_data.get("appointmentTime", "")
            
                if appointment_date_str and appointment_time_str:
                    # Convert appointment date string to datetime object
                    appointment_datetime = date.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
                
                    # Check if appointment date is in the future
                    if appointment_datetime >= date.datetime.now() and appointment_datetime < (date.datetime.now()+ timedelta(days=1)) and appointment_data["status"] == "Ongoing":
                        upcoming_appointments[appointment_id] = appointment_data

                for patient_id, patient_data in patients.items():
                    if appointment_data["patientName"] == patient_id:
                        for patientdata_id, patientdata_data in patientdatas.items():
                            if patientdata_data["status"] == 'Inpatient' and patientdata_id == appointment_data["patientName"]:
                            # if patientdata_data["status"] == 'Inpatient' and patientdata_data['patientid'] == appointment_data["patientName"]:
                                inpatients[patientdata_id] = patientdata_data       

        # Sort appointments by date
        sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_upcoming_appointments = {}

    chosenPatients= {}
    if patients:
        for patients_id, patients_data in patients.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patients_id == appointment_data['patientName']:
                    chosenPatients[patients_id] = patients_data


    chosenPatientData= {}
    if patientsdata:
        for patientsdata_id, patientsdata_data in patientsdata.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patientsdata_id == appointment_data['patientName']:
                    chosenPatientData[patientsdata_id] = patientsdata_data


    # Pass the combined data to the template
    return render(request, 'hmis/doctordashboard.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors,
                                                             'inpatients':inpatients, 'rooms': rooms, 'chosenPatientData': chosenPatientData,
                                                             'submittedTest':submittedTest,'patients1': chosenPatients}) 

def ChargeNurseDashboard(request):
    nurses = db.child("nurses").get().val()
    uid = request.session['uid'] 

    rooms = db.child("rooms").get().val()
    
    if request.method == 'POST':
        try:
            for room_id, room_data in rooms.items():
                morning = request.POST.get(f'morning_{room_id}')  
                afternoon = request.POST.get(f'afternoon_{room_id}')
                graveyard = request.POST.get(f'graveyard_{room_id}')
                # print(room_id)
                data = {
                    'nurse_assigned': {
                        'morning': morning,
                        'afternoon': afternoon,
                        'graveyard': graveyard,
                    }
                }
                db.child('rooms').child(room_id).update(data)

                messages.success(request, 'Room Assignments saved successfully!')
            return redirect('ChargeNurseDashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'hmis/ChargeNurseDashboard.html', {'nurses': nurses, 'uid': uid, 'rooms': rooms})

# def roomAssignments(request):
#     nurses = db.child("nurses").get().val()
#     uid = request.session['uid'] 

#     rooms = db.child("rooms").get().val()

#     if request.method == 'POST':
#         morning = request.POST.get('morning')  
#         afternoon = request.POST.get('afternoon')
#         graveyard = request.POST.get('graveyard')
#         id = request.POST.get('roomID')

#         try:
#             # Save to Firebase
#             data = {
#                 'nurse_assigned': {
#                     'morning': morning,
#                     'afternoon': afternoon,
#                     'graveyard': graveyard,
#                 }
#             }
#             db.child('rooms').child(id).set(data)

#             messages.success(request, 'Room Assignments saved successfully!')
#             return redirect('HeadNurseDashboard')
#         except Exception as e:
#             messages.error(request, f'Error: {str(e)}')
 
#     return render(request, 'hmis/HeadNurseDashboard.html', {'nurses': nurses, 'uid': uid, 'rooms': rooms})

def patient_data_doctor_view(request):
    # Fetch patients from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    appointments = db.child("appointments").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    rooms = db.child("rooms").get().val()

    chosenPatients= {}
    if patients:
        for patients_id, patients_data in patients.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patients_id == appointment_data['patientName']:
                    chosenPatients[patients_id] = patients_data

    chosenPatientData= {}
    if patientsdata:
        for patientsdata_id, patientsdata_data in patientsdata.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patientsdata_id == appointment_data['patientName']:
                    chosenPatientData[patientsdata_id] = patientsdata_data

    # Pass the patients data to the template
    return render(request, 'hmis/patient_data_doctor_view.html', {'patients': chosenPatients, 
                                                                  'chosenPatientData': chosenPatientData, 
                                                                  'doctors': doctors, 
                                                                  'uid': uid,
                                                                  'rooms': rooms})

def patient_personal_information_inpatient(request):
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    consulnotes = db.child("consultationNotes").get().val()
    progressnotes = db.child("progressnotes").get().val()

    date1 = datetime.today().strftime('%Y-%m-%d')
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    medications_cursor = collection.find({}, {"Disease": 1, "_id": 0})
    medicines_set = {medication['Disease'] for medication in medications_cursor}
    medicines_list = list(medicines_set)

    disease_cursor = collection.find({}, {"Disease": 1, "_id": 0})
    disease_set = {disease['Disease'] for disease in disease_cursor}
    disease_list = list(disease_set)
    
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']   

    time_slots = []
    next_available_dates = []
    list_final = []
    days_checked = 0
    current_date = datetime.now()

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    for appointment_id, appointment_data in upcomings.items():
        if appointment_data["doctorUID"] == uid:
            appointment_date_str = appointment_data.get("appointmentDate", "")
            appointment_time_str = appointment_data.get("appointmentTime", "")
        
            if appointment_date_str and appointment_time_str:
                appointment_datetime = date.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
            
                if appointment_datetime >= date.datetime.now() and appointment_data["status"] == "Ongoing":
                    upcoming_appointments[appointment_id] = appointment_data

    # Sort appointments by date
    sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    

    time_slots1 = []
    appointmentschedule_data1 = db.child("appointmentschedule").child(uid).get().val()
    if appointmentschedule_data1:
        available_days_str1 = appointmentschedule_data1.get("days", "")
        day_name_to_number1 = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }

        available_days_numbers1 = [day_name_to_number1[day.lower()] for day in available_days_str1 if day.lower() in day_name_to_number1]

        current_day_of_week1 = datetime.now().weekday()
        current_date1 = datetime.now() + timedelta(days=3)  # Start checking from three days ahead
        next_available_date1 = None  # Initialize the variable to store the next available date
        days_checked = 0  # Initialize days_checked variable
        while days_checked < 7:  # Check up to 7 days
            if current_day_of_week1 in available_days_numbers1:
                if current_date1.date():
                    next_available_date1 = current_date1.date()
                    break  # Exit the loop as soon as the first available date is found
            current_date1 += timedelta(days=1)
            current_day_of_week1 = (current_day_of_week1 + 1) % 7
            days_checked += 1

        next_available_date_str1 = next_available_date1.strftime('%Y-%m-%d')

        appointments_for_specific_date1 = [appointment_data for appointment_data in upcoming_appointments.values() if appointment_data['appointmentDate'] == next_available_date_str1]
        booked_time_slots1 = set(appointment['appointmentTime'] for appointment in appointments_for_specific_date1)
       
        # Define the start and end time for morning and afternoon appointments for the specific date
        morning_start = datetime.strptime(appointmentschedule_data1.get("morning_start"), '%H:%M')
        morning_end = datetime.strptime(appointmentschedule_data1.get("morning_end"), '%H:%M')
        afternoon_start = datetime.strptime(appointmentschedule_data1.get("afternoon_start"), '%H:%M')
        afternoon_end = datetime.strptime(appointmentschedule_data1.get("afternoon_end"), '%H:%M')
        
        interval = timedelta(minutes=30)
        
        # Calculate time slots for morning
        current_time1 = morning_start
        while current_time1 <= morning_end:
            # Check if the current time slot is not booked
            if current_time1.strftime('%I:%M %p') not in booked_time_slots1:
                time_slots1.append(current_time1.strftime('%I:%M %p'))  # Include AM/PM
            current_time1 += interval

        # Calculate time slots for afternoon
        current_time1 = afternoon_start
        while current_time1 <= afternoon_end:
            # Check if the current time slot is not booked
            if current_time1.strftime('%I:%M %p') not in booked_time_slots1:
                time_slots1.append(current_time1.strftime('%I:%M %p'))  # Include AM/PM
            current_time1 += interval



    
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
    if appointmentschedule_data:
        available_days_str = appointmentschedule_data.get("days", "")
        day_name_to_number = {
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,
            'sunday': 7
        }

        available_days_numbers = [day_name_to_number[day.lower()] for day in available_days_str if day.lower() in day_name_to_number]
        current_day_of_week = datetime.now().weekday()

        while len(next_available_dates) < 4 and days_checked < 60:  # Check up to 30 days
            if current_day_of_week in available_days_numbers:
                # Check if there are no appointments on this date
                if current_date.date() not in [datetime.strptime(appointment_data['appointmentDate'], "%Y-%m-%d").date() for appointment_data in upcoming_appointments.values()]:
                    list_final.append(current_date.date())

            current_date += timedelta(days=1)
            current_day_of_week = (current_day_of_week + 1) % 7
            days_checked += 1

        # Get current date
        current_date = datetime.now().date()
        three_days = current_date + timedelta(days=3)
        # Calculate dates 1 week, 2 weeks, 3 weeks, and 1 month from now
        
        one_week_from_now = current_date + timedelta(weeks=1)
        two_weeks_from_now = current_date + timedelta(weeks=2)
        three_weeks_from_now = current_date + timedelta(weeks=3)
        one_month_from_now = current_date + timedelta(days=30)

        # Define a threshold for finding the nearest date
        threshold = timedelta(days=3)  # Adjust as needed

        # Function to find the nearest date
        def find_nearest_date(target_date, dates_list):
            nearest_date = min(dates_list, key=lambda x: abs(x - target_date))
            return nearest_date

        # Find the nearest dates
        nearest_dates = {
            'one_week_from_now': find_nearest_date(one_week_from_now, list_final),
            'two_weeks_from_now': find_nearest_date(two_weeks_from_now, list_final),
            'three_weeks_from_now': find_nearest_date(three_weeks_from_now, list_final),
            'one_month_from_now': find_nearest_date(one_month_from_now, list_final)
        }
        
        three_days_after = find_nearest_date(three_days, list_final)
        # print('three_days_after', three_days_after)

        # Define time slots for morning
        morning_start_str = appointmentschedule_data.get("morning_start")
        morning_end_str = appointmentschedule_data.get("morning_end")

        # Convert strings to datetime objects for morning
        morning_start = datetime.strptime(morning_start_str, '%H:%M')
        morning_end = datetime.strptime(morning_end_str, '%H:%M')

        # Define time slots for afternoon
        afternoon_start_str = appointmentschedule_data.get("afternoon_start")
        afternoon_end_str = appointmentschedule_data.get("afternoon_end")

        # Convert strings to datetime objects for afternoon
        afternoon_start = datetime.strptime(afternoon_start_str, '%H:%M')
        afternoon_end = datetime.strptime(afternoon_end_str, '%H:%M')

        interval = timedelta(minutes=30)

        # Calculate time slots for morning
        current_time = morning_start
        while current_time <= morning_end:
            time_slots.append(current_time.strftime('%I:%M %p'))  # Include AM/PM
            current_time += interval

        # Calculate time slots for afternoon
        current_time = afternoon_start
        while current_time <= afternoon_end:
            time_slots.append(current_time.strftime('%I:%M %p'))  # Include AM/PM
            current_time += interval
    
    time_objects = [datetime.strptime(time_slot, '%I:%M %p') for time_slot in time_slots]

    # Find the earliest time slot
    if time_objects:
        earliest_time = min(time_objects)
        time_early = earliest_time.strftime('%I:%M %p')
        print("Earliest time slot:", time_early)
    else:
        print("No time slots available")

    chosenPatient = request.GET.get('chosenPatient', '')
    endAppointment = request.GET.get('appointmentID', '')

    past_appointments = {}
    for appointment_id, appointment_data in upcomings.items():
        if appointment_data["doctorUID"] == uid:
            appointment_date_str = appointment_data.get("appointmentDate", "")
            appointment_time_str = appointment_data.get("appointmentTime", "")
        
            if appointment_date_str and appointment_time_str:
            # Convert appointment date string to datetime object
                appointment_datetime = date.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
            
            # Check if appointment date is in the future
                if (appointment_datetime < date.datetime.now() or appointment_data["status"] == "Finished") and appointment_data["patientName"] == chosenPatient:
                    past_appointments[appointment_id] = appointment_data

    sorted_appointments = dict(sorted(past_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p"), reverse=True))

    # Fetch appointments from the database
    appointments = db.child("appointments").get().val()
    booked_times = set()

    # Exclude booked times from the available time slots
    for appointment_id, appointment_data in appointments.items():
        # if appointment_data["doctorUID"] == uid:
            if appointment_data["status"] == "Finished":
                appointment_date = appointment_data["appointmentDate"]
                appointment_time = appointment_data["appointmentTime"]
                appointment_datetime_str = f"{appointment_date} {appointment_time}"
                appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %I:%M %p')
                booked_times.add(appointment_datetime.strftime('%H:%M'))

    # Remove booked times from the available time slots
    time_slots = [time_slot for time_slot in time_slots if time_slot not in booked_times]

    chosenPatientData = {}
    for patients_id, patients_data in patients.items():
        if chosenPatient == patients_data["uid"]:
            chosenPatientData[patients_id] = patients_data

            #retrieve patient birthdate
            chosenPatientBirthday = chosenPatientData[chosenPatient].get("bday")
            #calculate patient age function
            # chosenPatientAge = calculate_age(chosenPatientBirthday)

    chosenPatientDatas = {}
    for patientsdata_id, patientsdata_data in patientsdata.items():
        if patientsdata_id == chosenPatient:
            chosenPatientDatas[patientsdata_id] = patientsdata_data

    #Get Vital Signs Data of Chosen Patient
    chosenPatientVitalEntryData = {}
    if vitalsigns:
        for vitalsigns_id, vitalsigns_data in vitalsigns.items():
            if chosenPatient == vitalsigns_id:
                for vsid, vsdata in vitalsigns_data.items():
                    chosenPatientVitalEntryData[vsid] = vsdata
        
        sorted_vital_signs = dict(sorted(chosenPatientVitalEntryData.items(), key=lambda item: date.datetime.strptime(item[1]['date'] + ' ' + item[1]['time'], "%Y-%m-%d %I:%M %p"), reverse=True))
    else:
        sorted_vital_signs = {}

    chosenPatientConsulNotes = {}

    consultation_notes_ref = db.child("consultationNotes").child(chosenPatient)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = consultation_notes_ref.child(date1).get().val()
    if consulnotes_data:
        chosenPatientConsulNotes[chosenPatient] = consulnotes_data
        if 'diagnosis' in consulnotes_data:
            currdiagnosis = consulnotes_data['diagnosis']
            medications_cursor = collection.find({}, {"Disease": 1, "_id": 0})
            medicines_set = {medication['Disease'] for medication in medications_cursor if medication['Disease'] == currdiagnosis}
            medicines_list = list(medicines_set)
        else:
            currdiagnosis = None

    # medications_cursor = collection.find({}, {"Disease": 1, "_id": 0})
    # medicines_set = {medication['Disease'] for medication in medications_cursor if medication['Disease'] == currdiagnosis}
    # medicines_list = list(medicines_set)

    cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2, "Strength": 3, "Route": 4})
    pharmacy_lists = [{'Drug': medication['Drug'], 'Strength': medication['Strength'], 'Route': medication['Route']} for medication in cursor]
    pharmacy_lists_json = json.dumps(pharmacy_lists)

    time_slots = []
    appointmentschedule = db.child("appointmentschedule").get().val()
    doctorSched = db.child("appointmentschedule").child(uid).get().val()
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
    
    formatted_dates = []
    for date_obj in next_available_dates:
        formatted_date = date_obj.strftime("%Y-%m-%d")
    
        # Append the formatted date to the list
        formatted_dates.append(formatted_date)        

    if appointmentschedule_data:
    # Define time slots for morning
        morning_start_str = appointmentschedule_data.get("morning_start")
        morning_end_str = appointmentschedule_data.get("morning_end")

        # Convert strings to datetime objects for morning
        morning_start = datetime.strptime(morning_start_str, '%H:%M')
        morning_end = datetime.strptime(morning_end_str, '%H:%M')

        # Define time slots for afternoon
        afternoon_start_str = appointmentschedule_data.get("afternoon_start")
        afternoon_end_str = appointmentschedule_data.get("afternoon_end")

        # Convert strings to datetime objects for afternoon
        afternoon_start = datetime.strptime(afternoon_start_str, '%H:%M')
        afternoon_end = datetime.strptime(afternoon_end_str, '%H:%M')

        interval = timedelta(minutes=30)

        # Calculate time slots for morning
        current_time = morning_start
        while current_time <= morning_end:
            time_slots.append(current_time.strftime('%H:%M'))
            current_time += interval

        # Calculate time slots for afternoon
        current_time = afternoon_start
        while current_time <= afternoon_end:
            time_slots.append(current_time.strftime('%H:%M'))
            current_time += interval

    
    if request.method == 'POST':
        
        if 'submitMedOrder' in request.POST:
            patient_uid = request.GET.get('chosenPatient')
            patientdata = db.child("patientdata").child(patient_uid).get().val()
            # print(patientdata)
            #numOfDays = int(request.POST.get('numOfDays'))
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            days = request.POST.getlist('days')
            numOfDays = 0
            for day in days:
                try:
                    day_int = int(day)
                    if day_int > numOfDays:
                        numOfDays = day_int
                except ValueError:
                    pass 

            # Calculate endDate
            todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
            endDate = todaydate_datetime + timedelta(days= numOfDays)
            endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

            patient_id = patient_uid 
            medicine_name = request.POST.getlist('medicine_name')
            dosage = request.POST.getlist('dosage')
            route = request.POST.getlist('route')
            
            #frequency = request.POST.getlist('frequency')
            
            additional_remarks = request.POST.getlist('additionalremarks')
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #times_list = []
            times = request.POST.getlist('times-daily[]')
            times_list = []

            # Iterate through the days and construct the times_list
            for day in days:
                times = request.POST.getlist('times-daily[]')
                times_str = ', '.join(times)
                times_list.append(times_str)

            try:
                id = str(uuid.uuid1())
                status = 'Ongoing'  # Default status

                # Check if endDate is reached
                if datetime.now() > endDate:
                    status = 'Finished'

                data = {
                    'prescriptionsorderUID': id,
                    'days': days,
                    'medicine_name': medicine_name,
                    'dosage': dosage,
                    'route': route,
                    #'frequency': occurence,
                    'times': times_list,
                    'additional_remarks': additional_remarks,
                    'patient_id': patient_id,
                    'todaydate': todaydate,
                    'endDate': endDate_str,
                    'status': status
                }
                db.child('prescriptionsorders').child(patient_id).child(todaydate).set(data)
                # print('STATUS ', patientdata['status'])
                if patientdata['status'] == 'Inpatient':
                    for index in range(len(medicine_name)):
                    
                        medicine = medicine_name[index]
                        dosage_value = dosage[index]
                        route_value = route[index]
                        additional_remarks_value = additional_remarks[index]
                        times_value = times_list[index]
                        days = int(days[index])

                        times_split = times_value.split(', ')
                        counter = len(times_split)

                        total = counter * days
                        for i in range(total):
                            pid = str(uuid.uuid1())
                            for j in range(len(times_split)):
                                data = {
                                    'date': endDate_str,
                                    'prescriptionsorderUID': id,
                                    'medicine_name': medicine,
                                    'dosage': dosage_value,
                                    'route': route_value,
                                    'additional_remarks': additional_remarks_value,
                                    'patient_id': patient_id,
                                    'todaydate': todaydate,
                                    'status': 'Ongoing',
                                    'days': days,
                                    'times': times[i].strip(),  # Save each time separately
                                    'total': total  # Total for this prescription
                                }
                                # Save to database
                                db.child('doctorsorders').child(patient_id).child(todaydate).child(pid).set(data)

                elif patientdata['status'] == 'Outpatient':
                    for index in range(len(medicine_name)):
                        medicine = medicine_name[index]
                        dosage_value = dosage[index]
                        route_value = route[index]
                        additional_remarks_value = additional_remarks[index]
                        times_value = times_list[index]
                        days = int(days[index])

                        times_split = times_value.split(', ')
                        counter = len(times_split)

                        total = counter * days
                        for i in range(total):
                            pid = str(uuid.uuid1())
                            for j in range(len(times_split)):
                                data = {
                                    'date': endDate_str,
                                    'prescriptionsorderUID': id,
                                    'medicine_name': medicine,
                                    'dosage': dosage_value,
                                    'route': route_value,
                                    'additional_remarks': additional_remarks_value,
                                    'patient_id': patient_id,
                                    'todaydate': todaydate,
                                    'status': 'Ongoing',
                                    'days': days,
                                    'times': times[i].strip(),  # Save each time separately
                                    'total': total  # Total for this prescription
                                }
                                # Save to database
                                db.child('patientsorders').child(patient_id).child(todaydate).child(pid).set(data)

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        if 'complaintButton' in request.POST:
            save_chiefComplaint(request)

        if 'rosButton' in request.POST:
            save_review_of_systems(request)

        if 'diagnosisButton' in request.POST:
            save_diagnosis(request)
        
        if 'submitLabTestRequest' in request.POST:
            id = str(uuid.uuid1())
            uid = request.session['uid'] 
            request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Retrieve the values of the checkboxes for each test
            blood_test = request.POST.get('bloodTestCheckbox', False)
            urine_test = request.POST.get('urineTestCheckbox', False)
            stool_test = request.POST.get('stoolTestCheckbox', False)
            tissue_biopsy = request.POST.get('tissueBiopsyCheckbox', False)
            xray = request.POST.get('xrayCheckbox', False)
            ct_scan = request.POST.get('ctScanCheckbox', False)
            mri = request.POST.get('mriCheckbox', False)
            ultrasound = request.POST.get('ultrasoundCheckbox', False)
            ecg = request.POST.get('ecgCheckbox', False)
            colonoscopy = request.POST.get('colonoscopyCheckbox', False)
            bronchoscopy = request.POST.get('bronchoscopyCheckbox', False)
            pet_scan = request.POST.get('petScanCheckbox', False)
            
            # Construct the data dictionary
            data = {
                'patient_id': chosenPatient,
                'datetime': request_time,
                'status': 'Ongoing',
                'blood_test': blood_test,
                'urine_test': urine_test,
                'stool_test': stool_test,
                'tissue_biopsy': tissue_biopsy,
                'xray': xray,
                'ct_scan': ct_scan,
                'mri': mri,
                'ultrasound': ultrasound,
                'ecg': ecg,
                'colonoscopy': colonoscopy,
                'bronchoscopy': bronchoscopy,
                'pet_scan': pet_scan,
                'doctor_id': uid 
            }
            
            # Save the data to the database
            db.child('testrequest').child(chosenPatient).set(data)


        if 'discharge_patient' in request.POST:
            numOfDays = request.POST.getlist('days') 
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
            qid = str(uuid.uuid1())

            todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
            
            times_list = []

            medicine_name = request.POST.getlist('medicineName1')
            dosage = request.POST.getlist('dosage1')
            route = request.POST.getlist('route1')
            frequency = request.POST.getlist('frequency1')
            additional_remarks = request.POST.getlist('remarks1')  
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # print(todaydate, chosenPatient, medicine_name, dosage, route, frequency, additional_remarks)
            selected_time = request.POST.get('selected_time')

            

            followUpDays = 0
            if selected_time == 'one_week':
                followUpDays = 7
            elif selected_time == 'two_weeks':
                followUpDays = 14
            elif selected_time == 'three_weeks':
                followUpDays = 21
            elif selected_time == 'one_month':
                followUpDays = 30
            
            endDate = todaydate_datetime + timedelta(days=followUpDays)
            endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

            
            appID = str(uuid.uuid1())
            appointment_date = request.POST.get('new-appointment-date')
            if appointment_date:
                appointment_time = request.POST.get('new-appointment-time')
                # Convert to datetime object
                time_obj = datetime.strptime(appointment_time, "%H:%M")

                # Convert to 12-hour format with AM/PM
                time_12h = time_obj.strftime("%I:%M %p")
                data1 = {
                    'appointmentDate': endDate_str,
                    'appointmentTime': time_12h,
                    'appointmentVisitType': 'Follow-Up Visit',
                    'doctorUID': uid,
                    'patientName': chosenPatient,
                    'status': 'Ongoing'
                }
                db.child('appointments').child(appID).set(data1)

            
            if medicine_name:
                db.child('prescriptionsorders').child(chosenPatient).child(todaydate).set(data)
            
            patientData = db.child("patientdata").child(chosenPatient).get().val()
            rooms = db.child("rooms").get().val()
            for room_id, room_data in rooms.items():
                if patientData['room'] == room_id:
                    room_patients = room_data.get('patients', [])

                    for patient in room_patients:
                        if chosenPatient == patient:
                            room_patients.remove(patient)
                            db.child("rooms").child(room_id).update({'patients': room_patients})
                            break

            db.child("patientdata").child(chosenPatient).update({
                                    'status': 'Outpatient',
                                    'room': None,
                                    'lastVisited': date1
                                })    
            new_id = str(uuid.uuid1())
            uid1 = request.session['uid'] 
            discharge_day = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pname = request.POST.get('pname')
            bday = request.POST.get('bday')
            gender = request.POST.get('gender')
            diagnosis = request.POST.get('diagnosis')
            attending_physician = request.POST.get('attending_physician')
            today_days_stay = request.POST.get('today_days_stay')
            selected_time = request.POST.get('selected_appointment_date')
            followup_time1 = request.POST.get('followup_time1')
            date_obj = datetime.strptime(selected_time, '%B %d, %Y')

            # Format the datetime object to the desired format (yyyy-mm-dd)
            formatted_date = date_obj.strftime('%Y-%m-%d')

            data = {
                'doctorid': uid1,
                'discharge_day': discharge_day,
                'pname': pname,
                'bday': bday,
                'gender': gender,
                'diagnosis': diagnosis,
                'attending_physician': attending_physician,
                'today_days_stay': today_days_stay,
                'patientid': chosenPatient 
            }
            
            # Save the data to the database
            db.child('admissionHistory').child(chosenPatient).child(discharge_day).set(data)

            data2 = {
                'appointmentDate': formatted_date,
                'appointmentTime': time_early,
                'appointmentVisitType': 'Follow-Up Visit',
                'doctorUID': uid1,
                'patientName': chosenPatient,
                'status': 'Ongoing'
            }
            db.child('appointments').child(new_id).set(data2)

            patient_uid = request.GET.get('chosenPatient')
            patientdata = db.child("patientdata").child(patient_uid).get().val()
            # print(patientdata)
            #numOfDays = int(request.POST.get('numOfDays'))
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            days = request.POST.getlist('days')
            numOfDays = 0
            for day in days:
                try:
                    day_int = int(day)
                    if day_int > numOfDays:
                        numOfDays = day_int
                except ValueError:
                    pass 

            # Calculate endDate
            todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
            endDate = todaydate_datetime + timedelta(days= numOfDays)
            endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

            patient_id = patient_uid 
            medicine_name = request.POST.getlist('medicine_name')
            dosage = request.POST.getlist('dosage')
            route = request.POST.getlist('route')
            
            #frequency = request.POST.getlist('frequency')
            
            additional_remarks = request.POST.getlist('additionalremarks')
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #times_list = []
            times = request.POST.getlist('times-daily[]')
            times_list = []

            # Iterate through the days and construct the times_list
            for day in days:
                times = request.POST.getlist('times-daily[]')
                times_str = ', '.join(times)
                times_list.append(times_str)

            return redirect(reverse('outpatient_medication_order') + f'?chosenPatient={chosenPatient}' + f'&diagnosis={currdiagnosis}')
 
        if 'admitButton' in request.POST:

            # currdiagnosis = request.POST.get("diagnosis")
             # Check if the patient is already an inpatient
            patient_data = db.child("patientdata").child(chosenPatient).get().val()
            if patient_data and patient_data.get('status') == 'Outpatient':
            # Get room occupancy data
                #room_occupancy = {}
                rooms = db.child("rooms").get().val()
                # Filter rooms that are not full and on the specified floor
                available_rooms = [room_id for room_id, room_data in rooms.items() if room_data.get('max_occupants', 0) > 0 
                               and room_data.get('fnumber') == 2
                               and len(room_data.get('patients', [])) < room_data.get('max_occupants', 0)]

            # If there are available rooms, assign the patient to a random available room
                if available_rooms:
                    chosen_room_id = random.choice(available_rooms)
                    room_data = rooms[chosen_room_id]
                    room_patients = room_data.get('patients', [])
                    room_patients.append(chosenPatient)
                    db.child("rooms").child(chosen_room_id).update({'patients': room_patients})


                    db.child("patientdata").child(chosenPatient).update({
                        'status': 'Inpatient',
                        'room': chosen_room_id
                    })

            #db.child("patientdata").child(chosenPatient).update({"status": "Inpatient",
                                                                 #'diagnosis': currdiagnosis,
                    
    
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    consulnotes = db.child("consultationNotes").get().val()
    # today = datetime.now()
    # tomorrow = today + timedelta(days=1)
    # date = tomorrow.strftime('%Y-%m-%d')
    date1 = datetime.today().strftime('%Y-%m-%d')
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    chosenPatient = request.GET.get('chosenPatient', '')

    appointmentschedule = db.child("appointmentschedule").get().val()

    chosenPatientData = {}
    for patients_id, patients_data in patients.items():
        if chosenPatient == patients_data["uid"]:
            chosenPatientData[patients_id] = patients_data

            #retrieve patient birthdate
            chosenPatientBirthday = chosenPatientData[chosenPatient].get("bday")
            #calculate patient age function
            # chosenPatientAge = calculate_age(chosenPatientBirthday)

    chosenPatientDatas = {}
    for patientsdata_id, patientsdata_data in patientsdata.items():
        if patientsdata_id == chosenPatient:
            chosenPatientDatas[patientsdata_id] = patientsdata_data

    #Get Vital Signs Data of Chosen Patient
    chosenPatientVitalEntryData = {}
    if vitalsigns:
        for vitalsigns_id, vitalsigns_data in vitalsigns.items():
            if chosenPatient == vitalsigns_id:
                for vsid, vsdata in vitalsigns_data.items():
                    chosenPatientVitalEntryData[vsid] = vsdata
        
        sorted_vital_signs = dict(sorted(chosenPatientVitalEntryData.items(), key=lambda item: date.datetime.strptime(item[1]['date'] + ' ' + item[1]['time'], "%Y-%m-%d %I:%M %p"), reverse=True))

    chosenPatientConsulNotes = {}
    # for consulnotes_id, consulnotes_data in consulnotes.items():
    #     if chosenPatient == consulnotes_data.data["patientID"] and date == consulnotes_data["date"]:
    #         chosenPatientConsulNotes[consulnotes_id] = consulnotes_data

    consultation_notes_ref = db.child("consultationNotes").child(chosenPatient)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = consultation_notes_ref.child(date1).get().val()
    if consulnotes_data:
        chosenPatientConsulNotes[chosenPatient] = consulnotes_data
        if 'diagnosis' in consulnotes_data:
            currdiagnosis = consulnotes_data['diagnosis']
            medications_cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2})
            medicines_set = {medication['Drug'] for medication in medications_cursor if medication['Disease'] == currdiagnosis}
            medicines_list = list(medicines_set)
        else:
            currdiagnosis = None                  

    # medications_cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2})
    # medicines_set = {medication['Drug'] for medication in medications_cursor if medication['Disease'] == currdiagnosis}
    # medicines_list = list(medicines_set)

    cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2, "Strength": 3, "Route": 4})
    pharmacy_lists = [{'Drug': medication['Drug'], 'Strength': medication['Strength'], 'Route': medication['Route']} for medication in cursor]
    pharmacy_lists_json = json.dumps(pharmacy_lists)
    
    progressnotes = db.child("progressnotes").get().val()
    nurses = db.child("nurses").get().val()

    # print('SORTED APPOINTMENTS ARE ', sorted_appointments)
    
    first_appointment = next(iter(sorted_appointments.values()), None)
    # print('FIRST APPOINTMENTS IS ', first_appointment)
    first_appointment_date = first_appointment['appointmentDate'] if first_appointment else None
    # print('CONVERTED FIRST DATE IS ', first_appointment_date)
    if first_appointment_date is None:
        num_days = 0
    else:
        given_date = datetime.strptime(first_appointment_date, '%Y-%m-%d')
        today_date = datetime.now()
        num_days = (today_date - given_date).days

        

    return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 
                                                                                'chosenPatientDatas': chosenPatientDatas, 
                                                                                'chosenPatientVitalEntryData': chosenPatientVitalEntryData,
                                                                                'chosenPatientConsulNotes': chosenPatientConsulNotes,
                                                                                'doctors': doctors,
                                                                                'uid': uid,
                                                                                'medicines_list': medicines_list,
                                                                                'appointmentschedule': appointmentschedule,
                                                                                'endAppointment': endAppointment,
                                                                                'progressnotes': progressnotes,
                                                                                'sorted_vital_signs': sorted_vital_signs,
                                                                                'consulnotes': consulnotes,
                                                                                'next_available_dates': next_available_dates,
                                                                                'num_days': num_days,
                                                                                'nurses': nurses,
                                                                                'nearest_dates': nearest_dates,
                                                                                'time_early': time_early,
                                                                                'three_days_after': three_days_after,
                                                                                'pharmacy_lists': pharmacy_lists_json,
                                                                                'time_slots1': time_slots1,
                                                                                'next_available_date_str1': next_available_date_str1,
                                                                                'disease_list': disease_list})

def save_chiefComplaint(request):
        
    #if request.method == 'POST':
        #uid = str(uuid.uuid1())
        date = datetime.today().strftime('%Y-%m-%d')
        chiefComplaint = request.POST.get('chiefComplaint')
        id = request.POST.get('complaintButton') 
        uid = request.session['uid'] 
        
        # Save Chief Compliant into Firebase Database
        appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

        # Update appointment data in Firebase
        if chiefComplaint:
            db.child(appointment_path).update({
                'patientID': id,
                'doctorID': uid,
                'chiefComplaint': chiefComplaint,
            })
    
def save_review_of_systems(request):
    date = datetime.today().strftime('%Y-%m-%d')
    skin_conditions = request.POST.getlist('skin_conditions')
    head_conditions = request.POST.getlist('head_conditions')
    eye_conditions = request.POST.getlist('eye_conditions')
    ear_conditions = request.POST.getlist('ear_conditions')
    nose_conditions = request.POST.getlist('nose_conditions')
    allergy_conditions = request.POST.getlist('allergy_conditions')
    mouth_conditions = request.POST.getlist('mouth_conditions')
    neck_conditions = request.POST.getlist('neck_conditions')
    breast_conditions = request.POST.getlist('breast_conditions')
    cardiac_conditions = request.POST.getlist('cardiac_conditions')
    gastro_conditions = request.POST.getlist('gastro_conditions')
    urinary_conditions = request.POST.getlist('urinary_conditions')
    pv_conditions = request.POST.getlist('pv_conditions')
    ms_conditions = request.POST.getlist('ms_conditions')
    neuro_conditions = request.POST.getlist('neuro_conditions')
    hema_conditions = request.POST.getlist('hema_conditions')
    endo_conditions = request.POST.getlist('endo_conditions')
    id = request.POST.get('rosButton')
    uid = request.session['uid'] 

    # Save into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

    # if not isinstance(skin_conditions, list):
    #     skin_conditions = [skin_conditions]
    #  Update appointment data in Firebase
    

    db.child(appointment_path).update({
        'patientID': id,
        'doctorID': uid,
        'review_of_systems': {
            'skin': skin_conditions,
            'head': head_conditions,
            'eyes': eye_conditions,
            'ear': ear_conditions,
            'nose': nose_conditions,
            'allergy': allergy_conditions,
            'mouth': mouth_conditions,
            'neck': neck_conditions,
            'breast': breast_conditions,
            'cardiac': cardiac_conditions,
            'gastro': gastro_conditions,
            'urinary': urinary_conditions,
            'pv': pv_conditions,
            'ms': ms_conditions,
            'neuro': neuro_conditions,
            'hema': hema_conditions,
            'endo': endo_conditions,
        }
    })

def save_diagnosis(request):
    date = datetime.today().strftime('%Y-%m-%d')
    diagnosis = request.POST.get('diagnosis')
    id = request.POST.get('diagnosisButton') 
    uid = request.session['uid']
    
    # Save Chief Compliant into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure
    appointment_path1 = f"/patientdata/{id}"  # Adjust the path as per your Firebase structure

    # Update appointment data in Firebase
    if diagnosis:
        db.child(appointment_path).update({
            'patientID': id,
            'doctorID': uid,
            'diagnosis': diagnosis
        })

        db.child(appointment_path1).update({
            'disease': diagnosis
        })


#Calculate age function for retrieving patient data

def calculate_age(birthday):
    today = datetime.today()
    # print(today)
    birthdate = datetime.strptime(birthday, '%Y-%m-%d').date()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def new_vital_sign_entry(request):
    patients = db.child("patients").get().val()

    chosenPatient = request.GET.get('chosenPatient', '')

    chosenPatientData = {}
    for patients_id, patients_data in patients.items():
        if chosenPatient == patients_data["uid"]:
            chosenPatientData[patients_id] = patients_data

            #retrieve patient birthdate
            chosenPatientBirthday = chosenPatientData[chosenPatient].get("bday")
            #calculate patient age function
            chosenPatientAge = calculate_age(chosenPatientBirthday)

    return render(request, 'hmis/new_vital_sign_entry.html', {'chosenPatientData': chosenPatientData, 'chosenPatientAge' : chosenPatientAge})


def patient_vital_signs_history(request):
    patients = db.child("patients").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    chosenPatient = request.GET.get('chosenPatient', '')

    chosenPatientData = {}
    for patients_id, patients_data in patients.items():
        if chosenPatient == patients_data["uid"]:
            chosenPatientData[patients_id] = patients_data

    #Get Vital Signs Data of Chosen Patient
    chosenPatientVitalEntryData = {}
    for vitalsigns_id, vitalsigns_data in vitalsigns.items():
        if chosenPatient == vitalsigns_id:
            for vsid, vsdata in vitalsigns_data.items():
                chosenPatientVitalEntryData[vsid] = vsdata
    
    sorted_vital_signs = dict(sorted(chosenPatientVitalEntryData.items(), key=lambda item: date.datetime.strptime(item[1]['date'] + ' ' + item[1]['time'], "%Y-%m-%d %I:%M %p"), reverse=True))
    return render(request, 'hmis/patient_vital_signs_history.html', {'chosenPatientData': chosenPatientData, 
                                                                     'chosenPatientVitalEntryData': chosenPatientVitalEntryData, 
                                                                     'doctors': doctors,
                                                                     'uid': uid,
                                                                     'vitalsigns': vitalsigns,
                                                                     'sorted_vital_signs': sorted_vital_signs})

def patient_medical_history(request):
    doctors = db.child("doctors").get().val()
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    consulNotes = db.child("consultationNotes").get().val()

    patientMedical = db.child("patientmedicalhistory").get().val()
    if request.method == 'POST':
        if 'saveMedicalHistoryButton' in request.POST:
            diagnosis_surgical = request.POST.getlist('diagnosis_surgical')
            date_illness = request.POST.getlist('date_illness')
            treatment = request.POST.getlist('treatment')
            remarks = request.POST.getlist('remarks')
            
            data = {
                'patient_id': chosen_patient_uid,
                'diagnosis_surgical': diagnosis_surgical,
                'date_illness': date_illness,
                'treatment': treatment,
                'remarks': remarks
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('pastHistory').update(data)

        if 'saveAllergyButton' in request.POST:
            allergen = request.POST.getlist('allergen')
            severity = request.POST.getlist('severity')
            
            data = {
                'patient_id': chosen_patient_uid,
                'allergen': allergen,
                'severity': severity
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('allergyhistory').update(data)

        if 'saveImmunizationButton' in request.POST:
            vaccine = request.POST.getlist('vaccine')
            date = request.POST.getlist('date')
            
            data = {
                'patient_id': chosen_patient_uid,
                'vaccine': vaccine,
                'date': date
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('immunizationHistory').update(data)

        if 'saveFamilyHistoryButton' in request.POST:
            family_member = request.POST.getlist('family_member')
            diagnosis = request.POST.getlist('diagnosis')
            age = request.POST.getlist('age')
            
            data = {
                'patient_id': chosen_patient_uid,
                'family_member': family_member,
                'diagnosis': diagnosis,
                'age': age
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('familyHistory').update(data)

        if 'saveSocialHistoryButton' in request.POST:
            smoking = request.POST.get('smoking')
            yearsSmoking = request.POST.get('smokingyears')
            #alcohol = request.POST.get('alcohol')
            print(smoking)
            data = {
                'patient_id': chosen_patient_uid,
                'smoking': smoking,
                'yearsSmoking': yearsSmoking
                #'alcohol': alcohol
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('socialHistory').update(data)

    return render(request, 'hmis/patient_medical_history.html', {'doctors': doctors,
                                                                 'uid': uid,
                                                                 'patientMedical': patientMedical,
                                                                 'chosenPatient': chosenPatient,
                                                                 'consulNotes': consulNotes})

from datetime import datetime

def view_treatment_plan_all(request):
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    patients = db.child("patients").get().val()
    selected_items = ['medicine_name', 'dosage', 'route', 'frequency', 'additional_remarks']
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    # Retrieve prescription orders for the chosen patient from Firebase
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid).get().val()
    
    dates = []
    if prescriptionsorders_ref:
        for order_date, order_data in prescriptionsorders_ref.items():
            # Convert date string to datetime object
            #date = datetime.strptime(order_date, '%Y-%m-%d')
            dates.append(order_date)
    
    sorted_dates = sorted(dates, reverse=True)
    # print(sorted_dates)
    
    # Get the latest date
    latest_date = sorted_dates[0] if sorted_dates else None
    # print(latest_date)

    chosenPatientTreatmentPlan = {}
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = prescriptionsorders_ref.child(latest_date).get().val()
    if consulnotes_data:
        chosenPatientTreatmentPlan[chosen_patient_uid] = consulnotes_data
    
    # print(chosenPatientTreatmentPlan)
    return render(request, 'hmis/view_treatment_plan.html', {
        'chosen_patient_uid': chosen_patient_uid,
        'patients': patients,
        'prescriptionsorders': chosenPatientTreatmentPlan,
        'latest_date': latest_date,
        'doctors': doctors,
        'uid': uid
    })

def view_treatment_plan(request, fname, lname, gender, bday):
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    return render(request, 'hmis/view_treatment_plan.html', {'fname': fname, 
                                                             'lname': lname, 
                                                             'gender': gender, 
                                                             'bday': bday, 
                                                             'doctors': doctors,
                                                             'uid': uid})

def patient_medication_doctor(request):
    # Fetch patients data from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()

    # Pass the combined data to the template
    return render(request, 'hmis/patient_medication_doctor.html', {'patients': patients, 'patientsdata': patientsdata})

def patient_medication_table(request):
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    prescriptionsorders = db.child("prescriptionorders").get().val()
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid).get().val()
    patients = db.child("patients").get().val()
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 
    return render(request, 'hmis/patient_medication_table.html', {'prescriptionsorders': prescriptionsorders, 
                                                                  'prescriptionsorders_ref': prescriptionsorders_ref,
                                                                  'patients': patients, 
                                                                  'chosen_patient_uid': chosen_patient_uid,
                                                                  'doctors': doctors,
                                                                  'uid': uid})

from django.http import JsonResponse
from paddleocr import PaddleOCR

# Function to extract the number of days
def extract_number_of_days(result):
    for sublist in result:
        if isinstance(sublist, list):
            num_days = extract_number_of_days(sublist)
            if num_days is not None:
                return num_days
        elif isinstance(sublist, tuple):
            word = sublist[0]
            # Use regular expression to find numerical value preceded by optional pound sign, followed by "days"
            days_match = re.search(r'#?\d+\s*days', word, flags=re.IGNORECASE)
            if days_match:
                days_value = int(re.findall(r'\d+', days_match.group())[0])
                return days_value
            
    return None


def extract_dosage(result):
    for sublist in result:
        if isinstance(sublist, list):
            dosage = extract_dosage(sublist)
            if dosage is not None:
                return dosage
        elif isinstance(sublist, tuple):
            word = sublist[0]
            # Use regular expression to find numerical value followed by "mg" or "mL" or "%cream"
            dosage_match = re.search(r'(\d+)\s*(mg|mL|%cream)', word, flags=re.IGNORECASE)
            if dosage_match:
                dosage_value = dosage_match.group(1)
                dosage_unit = dosage_match.group(2)
                # Combine dosage value and unit into a single string
                dosage = f"{dosage_value}{dosage_unit}"
                return dosage
    return None


# Function to extract the medicine names
def extract_medicine_names(result, medicine_names):
    extracted_medicines = []
    for sublist in result:
        if isinstance(sublist, list):
            extracted_medicines.extend(extract_medicine_names(sublist, medicine_names))
        elif isinstance(sublist, tuple):
            word = sublist[0]
            for medicine in medicine_names:
                if medicine.lower() in word.lower():
                    extracted_medicines.append(medicine)
    return extracted_medicines


def extract_routes_and_frequency(result):
    extracted_frequency = None
    for sublist in result:
        if isinstance(sublist, list):
            frequency = extract_routes_and_frequency(sublist)
            if frequency:  # Check if frequency is already extracted
                extracted_frequency = frequency
        elif isinstance(sublist, tuple):
            word = sublist[0]
            # Extract frequency
            if re.search(r'\bq\.d\.?\b', word, re.IGNORECASE):
                extracted_frequency = "Morning"
            elif re.search(r'\bb\.i\.d\.?\b', word, re.IGNORECASE):
                extracted_frequency = "Morning, Evening"
            elif re.search(r'\bt\.i\.d\.?\b', word, re.IGNORECASE):
                extracted_frequency = "Morning, Afternoon, Evening"
    return extracted_frequency


def extract_routes(result, routes):
    extracted_routes = []
    routeFinal = "Nal"  # Default value if no text in route is recognized
    for sublist in result:
        if isinstance(sublist, list):
            extracted, route = extract_routes(sublist, routes)
            extracted_routes.extend(extracted)
            if route == "Oral":
                routeFinal = "Oral"  # Update routeFinal if "Oral" is recognized
        elif isinstance(sublist, tuple):
            word = sublist[0]
            for route in routes:
                if route.lower() in word.lower():
                    extracted_routes.append(route)
                    routeFinal = "Oral"  # Set routeFinal to "Oral" when a word from the routes is recognized
    return extracted_routes, routeFinal

def perform_ocr(request):
    if request.method == 'POST' and request.FILES['image']:
        patient_uid = request.GET.get('chosenPatient')
        image = request.FILES['image'].read()

        # Initialize PaddleOCR with the desired language model
        ocr = PaddleOCR(use_angle_cls=True, lang='en')

        # Perform OCR on the image
        result = ocr.ocr(image, cls=True)

        # Extract the recognized text from the OCR result
        # recognized_text = '\n'.join([line[1][0] for line in result])

        for line in result:
            for word_info in line:
                print(word_info[1], end=" ")
            print() 


        medications_cursor = collection.find({}, {"_id": 0, "Drug": 1,})
        medicines_set = {medication['Drug'] for medication in medications_cursor}
        medicine_names = list(medicines_set)

        # medicine_names = [
        #     "Rosuvastatin", "Atorvastatin", "Amoxicillin", "Cefoxitin sodium",
        #     "Prednisolone", "Alprazolam", "HCTZ", "Metformin", "Glipizide",
        #     "Diclofenac", "Paracetamol", "Loratadine", "Montelukast", "Salbutamol",
        #     "Sitagliptin", "Clindamycin", "Hydroxyzine", "Diphenhydramine Hydrochloride",
        #     "Alvesco", "Glimepiride", "Co-Amoxiclav", "Propranolol", "Linagliptin",
        #     "Cetirizine", "Levocetirizine", "Desloratadine", "Ibuprofen", "Probucol",
        #     "Enalapril", "Diazepam", "Azithromycin", "Celecoxib", "Levofloxacin",
        #     "Ketoconazole", "Lorazepam", "Guaifenesin", "Clotrimazole", "Losartan",
        #     "Doxycycline", "Piroxicam"
        # ]

        routes = ["Tablet", "Oral", "Pills", "Capsule", "tasbels", "tablels", "P.O.", "p.o."]

        days_value = extract_number_of_days(result)
        dosage_value = extract_dosage(result)
        medicine_names_extracted = extract_medicine_names(result, medicine_names)
        extracted_frequency = extract_routes_and_frequency(result)
        extracted_routes, routeFinal = extract_routes(result, routes)

        # Print the extracted values
        print("Number of Days:", days_value)
        print("Dosage (mg):", dosage_value)
        print("Medicine Names:", medicine_names_extracted)
        print("Final Route:", routeFinal)
        print("Final Frequency:", extracted_frequency)

        id=str(uuid.uuid1())

        todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
        endDate = todaydate_datetime + timedelta(days=days_value)
        endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")
        days_str = str(days_value)

        data = {
            'days': [days_str],
            'dosage': [dosage_value],
            'medicine_name': medicine_names_extracted,
            'route': [routeFinal],
            'todaydate': todaydate,
            'prescriptionsorderUID': id,
            'status': 'Ongoing',
            'endDate': endDate_str,
            'times': [extracted_frequency],
            'patient_id': patient_uid
        }

        db.child('prescriptionsorders').child(patient_uid).child(todaydate).set(data)
        dosage_value = dosage_value
        route_value = routeFinal
        days = int(days_str)

        # Split the times_value into individual frequencies
        times_split = extracted_frequency.split(', ')

        # Calculate the total number of doses
        total_doses = len(times_split) * days

        for medicine in medicine_names_extracted:
            # Generate a unique prescription ID for each medicine
            

            # Iterate over each frequency (time) for the medicine
            for time_value in times_split:
                pid = str(uuid.uuid1())
                data = {
                    'date': endDate_str,
                    'prescriptionsorderUID': pid,
                    'medicine_name': medicine,
                    'dosage': dosage_value,
                    'route': route_value,
                    'patient_id': patient_uid,
                    'todaydate': todaydate,
                    'status': 'Ongoing',
                    'days': days,
                    'times': time_value.strip(),  # Save each time separately
                    'total': total_doses  # Total for this prescription
                }

                # Save to the database under the patient's orders
                db.child('patientsorders').child(patient_uid).child(todaydate).child(pid).set(data)


    return redirect(reverse('view_treatment_plan_all') + f'?chosenPatient={patient_uid}')

# from PIL import Image, ImageDraw, ImageFont

# def generate_prescription(doctor_name, patient_name, medication, dosage):
#     # Open prescription pad template
#     prescription_pad = Image.open('prescription_pad_template.png')

#     # Initialize drawing context
#     draw = ImageDraw.Draw(prescription_pad)

#     # Load font
#     font = ImageFont.truetype('arial.ttf', size=12)

#     # Define text and positions
#     doctor_text = f"Doctor: {doctor_name}"
#     patient_text = f"Patient: {patient_name}"
#     medication_text = f"Medication: {medication}"
#     dosage_text = f"Dosage: {dosage}"

#     # Draw text on the prescription pad
#     draw.text((50, 50), doctor_text, fill='black', font=font)
#     draw.text((50, 70), patient_text, fill='black', font=font)
#     draw.text((50, 90), medication_text, fill='black', font=font)
#     draw.text((50, 110), dosage_text, fill='black', font=font)

#     # Save the generated prescription
#     prescription_pad.save('generated_prescription.png')

# Example usage
# generate_prescription("Dr. Smith", "John Doe", "Aspirin", "Take one tablet daily")


def pharmacy_drugs(request):
    #collection = connect_to_mongodb()
    cursor = collection.find().limit(10)

    # Convert the cursor to a list of dictionaries
    data = list(cursor)
    # print(data)

    # Pass the data to the template for rendering
    return render(request, 'hmis/test.html', {'data': data})

def generate_unique_id():
    return str(uuid.uuid4())

def outpatient_medication_order(request):
    patients = db.child("patients").get().val()
    patient_uid = request.GET.get('chosenPatient')
    medications_cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2,})
    medicines_set = {medication['Drug'] for medication in medications_cursor}
    medicines_list = list(medicines_set)
    cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2, "Strength": 3, "Route": 4})
    pharmacy_lists = [{'Drug': medication['Drug'], 'Strength': medication['Strength'], 'Route': medication['Route']} for medication in cursor]
    pharmacy_lists_json = json.dumps(pharmacy_lists)
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 

    todaydate = datetime.now().strftime("%Y-%m-%d")
    clinics = db.child("clinics").get().val()

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patientData[patients_id] = patients_data


    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 
                                                                     'medicines_list': medicines_list, 
                                                                     'pharmacy_lists':pharmacy_lists_json,
                                                                     'patient_uid': patient_uid,
                                                                     'doctors': doctors,
                                                                     'uid': uid,
                                                                     'todaydate': todaydate,
                                                                     'clinics' :clinics, 
                                                                     'patientData': patientData,})


@csrf_exempt
def save_prescriptions(request):
    patient_uid = request.GET.get('chosenPatient')
    patients = db.child("patients").get().val()
    #patientdata = db.child("patientdata").child(patient_uid).get().val()
    todaydate = datetime.now().strftime("%Y-%m-%d")
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 
    clinics = db.child("clinics").get().val()

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patientData[patients_id] = patients_data

    patientName = patientData[patient_uid].get('fname','N/A') + ' ' + patientData[patient_uid].get('lname','N/A')
    patientGender = patientData[patient_uid].get('gender','N/A')
    patientAddress = patientData[patient_uid].get('address','N/A')

    for doctor_id, doctor_data in doctors.items():
        if uid == doctor_data["uid"]:
            doctorName = doctor_data["fname"] + ' ' + doctor_data["lname"]
            specialization = doctor_data["specialization"] 
            license = str(doctor_data["license"])
            ptr = str(doctor_data["ptr"])


    # Generate unique ID for the prescription
    prescription_id = str(uuid.uuid1())

    data = {
        'patient_name': patientName,
        'patient_age': request.POST.get('patient_age', 'N/A'),
        'patient_gender': patientGender,
        'patient_address': patientAddress,
        'date': todaydate,
        'medicines': {
            'name': request.POST.getlist('medicine_name'),
            'dosage': request.POST.getlist('dosage'),
            'route': request.POST.getlist('route'),
            'times': request.POST.getlist('times'),
            'days': request.POST.getlist('days'),
        },
        'doctor': doctorName,
        'specialization': specialization,
        'license': license,
        'ptr': ptr,
    }

    print(data)

    # Create the PDF
    temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_prescription.pdf')
    create_prescription_pdf(data, temp_file_path)

    try:
        # Upload the PDF to Firebase
        storage_path = 'prescriptions/prescription.pdf'
        upload_pdf_to_firebase(temp_file_path, storage_path)

        # Success message
        #return HttpResponse("Prescription created and uploaded successfully.")
        return redirect(reverse('view_treatment_plan_all') + f'?chosenPatient={patient_uid}')
    except Exception as e:
        return HttpResponse(f"An error occurred: {e}")
    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # patient_uid = request.GET.get('chosenPatient')
    
    # patientdata = db.child("patientdata").child(patient_uid).get().val()

    # if request.method == 'POST':
    #     uid = request.session['uid'] 

    #     todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     days = request.POST.get('days')
    #     numOfDays = max(map(int, days), default=0)

    #     todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
    #     endDate = todaydate_datetime + timedelta(days=numOfDays)
    #     endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

    #     patient_id = patient_uid 
    #     todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    #     medicine_names = request.POST.getlist('medicine_name[]')
    #     dosages = request.POST.getlist('dosage[]')
    #     days = request.POST.getlist('days[]')
    #     routes = request.POST.getlist('route[]')
    #     remarks = request.POST.getlist('remarks[]')
    #     times = request.POST.getlist('times[]')
    #     # print('routes is ', routes)
    #     # print('dosages is ', dosages)

    #     # Generate unique ID for the prescription
    #     prescription_id = str(uuid.uuid1())

    #     # Set default status
    #     status = 'Ongoing' if datetime.now() < endDate else 'Finished'

    #     # Construct prescription data
    #     prescription_data = {
    #         'prescriptionsorderUID': prescription_id,
    #         'days': days,
    #         'medicine_name': medicine_names,
    #         'dosage': dosages,
    #         'route': routes,
    #         'times': times,
    #         'additional_remarks': remarks,
    #         'patient_id': patient_id,
    #         'todaydate': todaydate,
    #         'endDate': endDate_str,
    #         'status': status,
    #     }
    #     # Save prescription data to the database
    #     db.child('prescriptionsorders').child(patient_id).child(todaydate).set(prescription_data)

    #     if patientdata['status'] == 'Outpatient':
    #         for index in range(len(medicine_names)):
    #             medicine = medicine_names[index]
    #             dosage_value = dosages[index]
    #             route_value = routes[index]
    #             additional_remarks_value = remarks[index]
    #             times_value = times[index]
    #             days_value = int(days[index])
    #             times_split = times_value.split(', ')
    #             counter = len(times_split)
    #             total = counter * days_value
    #             for time_value in times_split:
    #                 pid = str(uuid.uuid1())
                    
    #                 data = {
    #                     'date': endDate_str,
    #                     'prescriptionsorderUID': id,
    #                     'medicine_name': medicine,
    #                     'dosage': dosage_value,
    #                     'route': route_value,
    #                     'additional_remarks': additional_remarks_value,
    #                     'patient_id': patient_id,
    #                     'todaydate': todaydate,
    #                     'status': 'Ongoing',
    #                     'days': days_value,
    #                     'times': time_value.strip(),  # Save each time separately
    #                     'total': total  # Total for this prescription
    #                 }
    #                     # Save to database
    #                     # Remove non-serializable values from the data dictionary
    #                 serializable_data = {key: value for key, value in data.items() if isinstance(value, (str, int, float, list, dict, tuple))}
    #                 db.child('patientsorders').child(patient_id).child(todaydate).child(pid).set(serializable_data)




def diagnostic_imagery_reports(request):
    submittedTest = db.child("submittedTest").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    
    chosenPatient = request.GET.get('chosenPatient', '')
    return render(request, 'hmis/diagnostic_imagery_reports.html', {'submittedTest': submittedTest, 'chosenPatient': chosenPatient, 'doctors': doctors, 'uid': uid})



def download_image(url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    return None

def create_prescription_pdf(data, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Set the margins
    margin = 0.5 * inch

    # Draw header
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - margin - 0.5 * inch, data['doctor'] + ", M.D.")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - margin - 0.8 * inch, data['specialization'])
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - margin - 1.1 * inch, "09168794532")
    c.drawCentredString(width / 2, height - margin - 1.3 * inch, "Clinic Hours: Monday - Friday | 9:00AM - 12:00NN")
    c.drawCentredString(width / 2, height - margin - 1.5 * inch, "              Sunday          | By Appointment")

    # Add a break line before the line
    c.line(margin, height - margin - 1.8 * inch, width - margin, height - margin - 1.8 * inch)

     # Draw patient details
    c.setFont("Helvetica-Bold", 12)
    patient_info_y = height - 2.5 * inch
    c.drawString(margin, patient_info_y, "Patient Name:")
    c.setFont("Helvetica", 12)
    c.drawString(margin + 1.25 * inch, patient_info_y, data['patient_name'])
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(3.5 * inch + 0.5 * inch, patient_info_y, "Age:")
    c.setFont("Helvetica", 12)
    c.drawString(3.5 * inch + 1.0 * inch, patient_info_y, data['patient_age'])
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - margin - 1.7 * inch, patient_info_y, "Gender:")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - margin - 1.0 * inch, patient_info_y, data['patient_gender'])

    patient_info_y -= 0.25 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, patient_info_y, "Address:")
    c.setFont("Helvetica", 12)
    c.drawString(margin + 1.25 * inch, patient_info_y, data['patient_address'])
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - margin - 1.9 * inch, patient_info_y, "Date:")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - margin - 0.7 * inch, patient_info_y, data['date'])

    # Draw logo below the address
    logo_url = 'https://seeklogo.com/images/R/RX-logo-1057A9CD42-seeklogo.com.png'
    logo_path = download_image(logo_url, 'logo.png')
    if logo_path:
        logo_size = 0.8 * inch
        c.drawImage(logo_path, (width - logo_size) / 10, height - 4.0 * inch, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
        os.remove(logo_path)

    # Draw prescription details
    y_position = height - 4.0 * inch
    indent = margin + 2.0 * inch
    for name, dosage, route, times, days in zip(data['medicines']['name'], 
                                                data['medicines']['dosage'], 
                                                data['medicines']['route'], 
                                                data['medicines']['times'], 
                                                data['medicines']['days']):
        c.setFont("Helvetica", 13)
        c.drawString(indent , y_position, f"Medicine Name: {name}")
        c.drawString(indent + 3.0 * inch, y_position, f"Dosage: {dosage}")
        y_position -= 0.2 * inch
        c.drawString(indent, y_position, f"Route: {route}")
        c.drawString(indent + 1.5 * inch, y_position, f"Times: {times}")
        c.drawString(indent + 3.0 * inch, y_position, f"Days: {days}")
        y_position -= 0.4 * inch  # Extra space between different medicines

    # Add two break lines before the footer
    y_position -= 0.6 * inch

    # Draw footer (right-aligned)
    footer_text = [
        "Doctor's Signature: ___________",
        "License No.: " + data['license'],
        "PTR No.: " +  data['ptr'],
    ]
    for i, text in enumerate(footer_text):
        c.setFont("Helvetica", 12)
        c.drawRightString(width - margin, y_position - (i + 1) * 0.3 * inch, text)

    c.showPage()
    c.save()

def upload_pdf_to_firebase(file_path, storage_path):
    firebase_storage.child(storage_path).put(file_path)

@csrf_exempt
def requestTest(request):
    patient_uid = request.GET.get('chosenPatient')
    patients = db.child("patients").get().val()
    #patientdata = db.child("patientdata").child(patient_uid).get().val()
    todaydate = datetime.now().strftime("%Y-%m-%d")
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 
    clinics = db.child("clinics").get().val()

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patientData[patients_id] = patients_data

    patientName = patientData[patient_uid].get('fname','N/A') + ' ' + patientData[patient_uid].get('lname','N/A')
    patientGender = patientData[patient_uid].get('gender','N/A')
    patientAddress = patientData[patient_uid].get('address','N/A')

    for doctor_id, doctor_data in doctors.items():
        if uid == doctor_data["uid"]:
            doctorName = doctor_data["fname"] + ' ' + doctor_data["lname"]
            specialization = doctor_data["specialization"] 
            license = str(doctor_data["license"])
            ptr = str(doctor_data["ptr"])


    if request.method == 'POST':

        # Generate unique ID for the prescription
        prescription_id = str(uuid.uuid1())

        data = {
            'patient_name': patientName,
            'patient_age': request.POST.get('patient_age', 'N/A'),
            'patient_gender': patientGender,
            'patient_address': patientAddress,
            'date': todaydate,
            'medicines': {
                'name': request.POST.getlist('medicine_name'),
                'dosage': request.POST.getlist('dosage'),
                'route': request.POST.getlist('route'),
                'times': request.POST.getlist('times'),
                'days': request.POST.getlist('days'),
            },
            'doctor': doctorName,
            'specialization': specialization,
            'license': license,
            'ptr': ptr,
        }

        print(data)

        # Create the PDF
        temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_prescription.pdf')
        create_prescription_pdf(data, temp_file_path)

        try:
            # Upload the PDF to Firebase
            storage_path = 'prescriptions/prescription.pdf'
            upload_pdf_to_firebase(temp_file_path, storage_path)

            # Success message
            return HttpResponse("Prescription created and uploaded successfully.")
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")
        finally:
            # Ensure the temporary file is deleted
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return render(request, 'hmis/requestTest.html' , {'patientData': patientData,
                                                        'patient_uid': patient_uid,
                                                        'doctors': doctors,
                                                        'clinics': clinics,
                                                        'uid': uid,
                                                        'todaydate': todaydate})
