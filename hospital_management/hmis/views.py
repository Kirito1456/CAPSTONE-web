from collections import defaultdict
from datetime import datetime , timedelta
import datetime as date
import re
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database, storage as firebase_storage
from hmis.forms import StaffRegistrationForm, AppointmentScheduleForm, MedicationsListForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import logout as auth_logout
from django.core.mail import send_mail
import random
from operator import itemgetter

from hmis.models import Medications, Notification
from hospital_management.settings import collection 
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage

import uuid
import json

from django.http import HttpResponse, JsonResponse
from PIL import Image
import base64
from firebase_admin import db

from io import BytesIO
from django.template.loader import get_template

# Use the firebase_database object directly
db = firebase_database

# views.py
import firebase_admin
from firebase_admin import storage
from .forms import ImageUploadForm


import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
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
    # storage = messages.get_messages(request)
    # storage.used = True

    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = firebase_auth.sign_in_with_email_and_password(email, password)
            session_id = user['localId']
            request.session['uid'] = str(session_id)

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
            complete = False
            for doctor_id, doctor_data in doctors.items():
                if session_id == doctor_id:
                    doctor_found = True
                    if doctor_data.get('license'):
                        complete = True

            if doctor_found and complete == True:
                return redirect('DoctorDashboard')
            elif doctor_found and complete == False:
                return redirect('newuser')
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



def register(request):
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them
    
    return render(request, 'hmis/register.html')

def newuser(request):

    if request.method == 'POST':
        license = request.POST.get('license')
        ptr = request.POST.get('ptr')
        uid = request.session.get('uid')
        doctors = db.child("doctors").get().val()

        for doctor_id, doctor_data in doctors.items():
            if doctor_id == uid:
                data = {
                    'license': license,
                    'ptr': ptr,
                }

                db.child('doctors').child(uid).update(data)
                return redirect('DoctorDashboard')

    return render(request, 'hmis/newuser.html')

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
                # Create user in Firebase Authentication
                user = firebase_auth.create_user_with_email_and_password(email, password)
                
                data = {
                    'uid': user['localId'],
                    'fname': cleaned_data['fname'],
                    'lname': cleaned_data['lname'],
                    'sex': cleaned_data['sex'],
                    'specialization': cleaned_data['specialization'],
                    #'department': cleaned_data['department'],
                    #'clinic': clinic,
                    'email': email,
                }

                db.child('doctors').child(user['localId']).set(data)
                               
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
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them

    # Fetch doctors and nurses data from Firebase
    doctors = db.child("doctors").get().val()
    clinics = db.child("clinics").get().val()
    uid = request.session['uid'] 
    
    return render(request, 'hmis/Profile.html', {'uid': uid, 'accounts': doctors, 'clinics': clinics})

def update_profile (request):
    if request.method == 'POST':
        try:
            uid = request.POST.get('update')
            new_clinics = request.POST.getlist('newclinic')

            # Construct the path to the appointment data in Firebase
            db_path = f"/doctors/{uid}"

            doctor_data = db.child(db_path).get().val()

            existing_clinics = doctor_data.get('clinic', [])

            updated_clinics = list(set(existing_clinics + new_clinics))

            # Update appointment data in Firebase
            db.child(db_path).update({
                'clinic': updated_clinics
            }) 
            messages.success(request, 'You have successfully joined clinics')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('Profile')  # Redirect to the profile page

    # Handle GET request or invalid form submission
    return redirect('Profile')

def get_clinic_doctor_list():
    clinics_ref = db.child("clinics").get().val()
    doctors_ref = db.child("doctors").get().val()

    clinic_doctor_list = []

    # Iterate through each clinic
    for clinic_id, clinic_data in clinics_ref.items():
        doctor_names = []

        # Iterate through each doctor
        for doctor_id, doctor_data in doctors_ref.items():
            if 'clinic' in doctor_data:
                # Check if the doctor's clinics contain the current clinic ID
                if clinic_id in doctor_data['clinic']:  # Check directly against the list
                    # Add doctor's full name to the list
                    doctor_names.append(f"{doctor_data['fname']} {doctor_data['lname']}")

        # Append to the clinic_doctor_list
        clinic_doctor_list.append({
            'clinic_id': clinic_id,
            'name': clinic_data['name'],
            'doctorNames': doctor_names,
        })

    return clinic_doctor_list

def get_next_available_date(available_days_numbers):
    current_day_of_week = datetime.now().weekday()
    current_date = datetime.now()
    next_available_date = None

    days_checked = 0
    while days_checked < 7:
        if current_day_of_week in available_days_numbers:
            next_available_date = current_date.date()
            break
        current_date += timedelta(days=1)
        current_day_of_week = (current_day_of_week + 1) % 7
        days_checked += 1

    return next_available_date

def get_available_time_slots(clinic_data, booked_time_slots):
    time_slots = []

    morning_start = datetime.strptime(clinic_data["morning_start"], '%H:%M')
    morning_end = datetime.strptime(clinic_data["morning_end"], '%H:%M')
    afternoon_start = datetime.strptime(clinic_data["afternoon_start"], '%H:%M')
    afternoon_end = datetime.strptime(clinic_data["afternoon_end"], '%H:%M')

    interval = timedelta(minutes=30)

    # Calculate time slots for morning
    current_time = morning_start
    while current_time <= morning_end:
        if current_time.strftime('%I:%M %p') not in booked_time_slots:
            time_slots.append(current_time.strftime('%I:%M %p'))
        current_time += interval

    # Calculate time slots for afternoon
    current_time = afternoon_start
    while current_time <= afternoon_end:
        if current_time.strftime('%I:%M %p') not in booked_time_slots:
            time_slots.append(current_time.strftime('%I:%M %p'))
        current_time += interval

    return time_slots

def get_clinic_schedule(uid, upcoming_appointments):
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
    
    day_name_to_number = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    clinic_data_list = []
    clinics = db.child("clinics").get().val()

    if appointmentschedule_data:
        for clinic_id, clinic_data in appointmentschedule_data.items():
            for id, data in clinics.items():
                if id == clinic_id:
                    name = data['name']
            available_days_numbers = []
            if 'days' in clinic_data:
                for day_name in clinic_data['days']:
                    available_days_numbers.append(day_name_to_number[day_name.lower()])

            next_available_date = get_next_available_date(available_days_numbers)
            if next_available_date is not None:
                next_available_date_str = next_available_date.strftime('%Y-%m-%d')
            else:
                next_available_date_str = "No available date within the next 7 days"

            # Fetch booked appointments for the specific date
            appointments_for_specific_date = [appointment_data for appointment_data in upcoming_appointments.values() if appointment_data['appointmentDate'] == next_available_date_str]
            booked_time_slots = set(appointment['appointmentTime'] for appointment in appointments_for_specific_date)

            time_slots = get_available_time_slots(clinic_data, booked_time_slots)

            clinic_data_list.append({
                'clinic_id': clinic_id,
                'name': name,
                'next_available_date_str': next_available_date_str,
                'time_slots': time_slots
            })
    else:
        clinic_data_list = []

    return clinic_data_list

def AppointmentUpcomingNotif(request, notification_id):
    if request.session.get('uid') is None:
        return redirect('home')
    
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']
    clinics = db.child("clinics").get().val()

    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    if upcomings:
        for appointment_id, appointment_data in upcomings.items():
            if appointment_data["doctorUID"] == uid:
                appointment_date_str = appointment_data.get("appointmentDate", "")
                appointment_time_str = appointment_data.get("appointmentTime", "")
            
                if appointment_date_str and appointment_time_str:
                    # Convert appointment date string to datetime object
                    appointment_datetime = datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
                
                    # Check if appointment date is in the future
                    if appointment_datetime >= datetime.now() and (appointment_data["status"] == "Confirmed" or appointment_data["status"] == "Pending"):
                        upcoming_appointments[appointment_id] = appointment_data

        # Sort appointments by date
        sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_upcoming_appointments = {}

    selected_date = request.GET.get('selected_date')
    if selected_date:
        # Convert selected date string to datetime object
        selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
        # Filter appointments by the selected date
        sorted_upcoming_appointments = {k: v for k, v in sorted_upcoming_appointments.items() if datetime.strptime(v['appointmentDate'], "%Y-%m-%d").date() == selected_datetime.date()}

    clinic_data_list = get_clinic_schedule(uid, sorted_upcoming_appointments)
    
    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentUpcoming.html', {
        'appointments': sorted_upcoming_appointments,
        'patients': patients,
        'uid': uid,
        'doctors': doctors,
        'clinics': clinics,
        'clinic_data_list': clinic_data_list,
        'notifications': notifications
    })

def AppointmentUpcoming(request):
    if request.session.get('uid') is None:
        return redirect('home')
    
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them
    
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']
    clinics = db.child("clinics").get().val()

    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    clinic_schedule = db.child("appointmentschedule").child(uid).get().val()
    available_days = set()
    if clinic_schedule:
        for clinic_id, clinic_data in clinic_schedule.items():
            days = clinic_data.get('days', [])
            available_days.update(days)

    available_days_list = list(available_days)

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    if upcomings:
        for appointment_id, appointment_data in upcomings.items():
            if appointment_data["doctorUID"] == uid:
                appointment_date_str = appointment_data.get("appointmentDate", "")
                appointment_time_str = appointment_data.get("appointmentTime", "")
            
                if appointment_date_str and appointment_time_str:
                    # Convert appointment date string to datetime object
                    appointment_datetime = datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
                
                    # Check if appointment date is in the future
                    if appointment_datetime >= datetime.now() and (appointment_data["status"] == "Confirmed" or appointment_data["status"] == "Pending"):
                        upcoming_appointments[appointment_id] = appointment_data

        # Sort appointments by date
        sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_upcoming_appointments = {}
    
    selected_date = request.GET.get('selected_date')
    if selected_date:
        # Convert selected date string to datetime object
        selected_datetime = datetime.strptime(selected_date, "%Y-%m-%d")
        # Filter appointments by the selected date
        sorted_upcoming_appointments = {k: v for k, v in sorted_upcoming_appointments.items() if datetime.strptime(v['appointmentDate'], "%Y-%m-%d").date() == selected_datetime.date()}


    clinic_data_list = get_clinic_schedule(uid, sorted_upcoming_appointments)
    
    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentUpcoming.html', {
        'appointments': sorted_upcoming_appointments,
        'patients': patients,
        'uid': uid,
        'doctors': doctors,
        'clinics': clinics,
        'clinic_data_list': clinic_data_list,
        'notifications': notifications,
        'selected_date' : selected_date,
        'available_days_list': available_days_list
    })

def update_appointment(request):    
    uid = request.session['uid'] 

    if request.method == 'POST':
        try:
            appID = request.POST.get('appID')
            new_clinic = request.POST.get('selected_clinic_id')
            new_time = request.POST.get('new_appointment_time')
            new_date = request.POST.get('selected_appointment_date')

            # Fetch the booked time slots for the selected date and clinic
            upcoming_appointments = db.child('appointments').get().val()
            booked_time_slots = set()
            if upcoming_appointments:
                for appointment_data in upcoming_appointments.values():
                    if (appointment_data['appointmentDate'] == new_date and 
                        appointment_data['clinicUID'] == new_clinic):
                        booked_time_slots.add(appointment_data['appointmentTime'])

            # Check if the new time is already booked
            if new_time in booked_time_slots:
                # Find the nearest available time slot
                clinic_data = db.child('appointmentschedule').child(uid).child(new_clinic).get().val()
                available_time_slots = get_available_time_slots(clinic_data, booked_time_slots)

                # Find the nearest available time slot
                new_time = find_nearest_available_time(new_time, available_time_slots)

            data = {
                'appointmentDate': new_date,
                'clinicUID': new_clinic,
                'appointmentTime': new_time,
                'status': 'Pending',
            }
            db.child('appointments').child(appID).update(data)
            messages.success(request, 'Rescheduled Appointment successfully requested')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('AppointmentUpcoming')  # Redirect to the appointments list page

    # Handle GET request or invalid form submission
    return redirect('AppointmentUpcoming')

def find_nearest_available_time(requested_time, available_time_slots):
    requested_time_dt = datetime.strptime(requested_time, '%I:%M %p')
    print('requested_time_dt is ', requested_time_dt)

    min_diff = None
    nearest_time = None
    for slot in available_time_slots:
        slot_dt = datetime.strptime(slot, '%I:%M %p')
        diff = abs((slot_dt - requested_time_dt).total_seconds())
        if min_diff is None or diff < min_diff:
            min_diff = diff
            nearest_time = slot

    return nearest_time

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
    appID = request.GET.get('appointmentID', '')
    appointmentschedule = db.child("appointmentschedule").child(uid).get().val()
    appointments = db.child("appointments").get().val()
    clinicId = ''

    DAY_NAME_TO_NUMBER = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    if request.method == 'POST':
        endAppointmentPatientID = request.POST.get('followupCheckbox')
        endAppointmentAPP = request.POST.get('endingAppointment')
        print('endAppointmentAPP is ', endAppointmentAPP)
        for id, data in appointments.items():

            if id == endAppointmentAPP:
                clinicId = data.get('clinicUID', '')
                appointmentTime = data.get('appointmentTime', '')
                break
        db.child("appointments").child(endAppointmentAPP).update({'status': 'Finished'})
        messages.success(request, 'Appointment ended successfully')


        if endAppointmentPatientID:
            id = str(uuid.uuid1())

            reoccuring = request.POST.get('reoccuringCheckbox')
            available_days = set()
            if appointmentschedule:
                for clinic_id, clinic_data in appointmentschedule.items():
                    days = clinic_data.get('days', [])
                    available_days.update(days)

            def get_nearest_valid_date(date, available_days):
                # Adjust the date to the nearest valid day
                day_of_week = date.weekday()
                available_days = {DAY_NAME_TO_NUMBER[day] for day in available_days} 
                if day_of_week in available_days:
                    return date
                # Find the nearest valid day
                for i in range(1, 8):
                    next_day = (day_of_week + i) % 7
                    if next_day in available_days:
                        return date + timedelta(days=i)
                return date

            # Single follow-up appointment
            if not reoccuring:
                # for one time appointments
                new_date_str = request.POST.get('follow_up_date')
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d")
                formatted_date = new_date.strftime("%Y-%m-%d")

                booked_time_slots = set()
                if appointments:
                    for appointment_data in appointments.values():
                        if (appointment_data['appointmentDate'] == formatted_date and 
                            appointment_data['clinicUID'] == clinicId):
                            booked_time_slots.add(appointment_data['appointmentTime'])
                

                # Check if the desired appointment time is already booked
                if appointmentTime in booked_time_slots:
                    # Find the nearest available time slot
                    clinic_data = db.child('appointmentschedule').child(uid).child(clinicId).get().val()
                    available_time_slots = get_available_time_slots(clinic_data, booked_time_slots)
                    appointmentTime = find_nearest_available_time(appointmentTime, available_time_slots)

                data = {
                    'appointmentDate': formatted_date,
                    'appointmentTime': appointmentTime,
                    'status': 'Confirmed',
                    'doctorUID': uid,
                    'appointmentVisitType': "Follow-Up Visit",
                    'clinicUID': clinicId,
                    'patientName': chosenPatient
                }
                db.child("appointments").child(id).set(data)
                messages.success(request, 'Follow up appointment successfully scheduled')
            else:
                interval = request.POST.get('follow_up_interval')

                intervals = {
                    '1_month': 1,
                    '3_months': 3,
                    '6_months': 6
                }
                interval_months = intervals.get(interval, 3) 
                date1 = datetime.today()
                
                for _ in range(4):  # Add appointments for the next 1 year
                    date1 += timedelta(days=interval_months * 30)
                    nearest_date = get_nearest_valid_date(date1, available_days)

                    booked_time_slots = set()
                    if appointments:
                        for appointment_data in appointments.values():
                            if (appointment_data['appointmentDate'] == nearest_date.strftime('%Y-%m-%d') and 
                                appointment_data['clinicUID'] == clinicId):
                                booked_time_slots.add(appointment_data['appointmentTime'])

                    # Check if the desired appointment time is already booked
                    if appointmentTime in booked_time_slots:
                        # Find the nearest available time slot
                        clinic_data = db.child('appointmentschedule').child(uid).child(clinicId).get().val()
                        available_time_slots = get_available_time_slots(clinic_data, booked_time_slots)
                        appointmentTime = find_nearest_available_time(appointmentTime, available_time_slots)

                    data = {
                        'appointmentDate': nearest_date.strftime('%Y-%m-%d'),
                        'appointmentTime': appointmentTime,
                        'status': 'Confirmed',
                        'doctorUID': uid,
                        'appointmentVisitType': "Follow-Up Visit",
                        'clinicUID': clinicId,
                        'patientName': chosenPatient
                    }
                    db.child("appointments").child(str(uuid.uuid1())).set(data)
                messages.success(request, 'Follow up appointments successfully scheduled')
        
        return redirect('DoctorDashboard')  # Redirect to the appointments list page

    return render(request, 'hmis/AppointmentUpcoming.html', {'uid': uid, 'appointmentschedule': appointmentschedule})

        
def AppointmentPast(request):

    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    pasts = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    consulNotes = db.child("consultationNotes").get().val()
    uid = request.session['uid']
    clinics = db.child("clinics").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)


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
        sorted_past_appointments = dict(sorted(past_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p"), reverse=True))
    else:
        sorted_past_appointments = {}
    
    print(sorted_past_appointments)
    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentPast.html', {'appointments': sorted_past_appointments, 'patients': patients,
                                                         'uid': uid, 'doctors': doctors, 'clinics': clinics, 'notifications': notifications})
    
def AppointmentCalendar(request):
    
    if request.session.get('uid') is None:
        return redirect('home')
    
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']

    id = request.session.get('uid')
    patients = db.child("patients").get().val()
    appointments = db.child("appointments").get().val()
    clinics = db.child("clinics").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

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
    
    return render(request, 'hmis/AppointmentCalendar.html', {'uid': uid, 'doctors': doctors, 'task_json': task_json, 'clinics': clinics, 'notifications': notifications})

def parse_time(time_str):
    return datetime.datetime.strptime(time_str, '%H:%M') if time_str else None

def AppointmentScheduling(request):
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them
    doctors = db.child("doctors").get().val()
    
    clinics = db.child("clinics").get().val()
    uid = request.session.get('uid')
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    # Fetch appointment schedule data
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val() or {}

    clinic_schedules = {}
    for clinic_id, clinic_data in appointmentschedule_data.items():
        selected_days = clinic_data.get('days', [])
        morning_start = clinic_data.get('morning_start', "")
        morning_end = clinic_data.get('morning_end', "")
        afternoon_start = clinic_data.get('afternoon_start', "")
        afternoon_end = clinic_data.get('afternoon_end', "")
        
        clinic_schedules[clinic_id] = {
            'selected_days': selected_days,
            'morning_start': morning_start,
            'morning_end': morning_end,
            'afternoon_start': afternoon_start,
            'afternoon_end': afternoon_end
        }

    # Define the days of the week
    days_of_week = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    found_clinic = False
    for doctors_id, doctors_data in doctors.items():
        if doctors_id == uid:
            if doctors_data.get('clinic'):
                for doctorClinic in doctors_data['clinic']:
                    if doctorClinic in clinics:
                        found_clinic = True
                        break
                if found_clinic:
                    break

    if request.method == 'POST':
        clinic = request.POST.get('clinic')
        selected_days = request.POST.getlist(f'selected_days_{clinic}')  # Get list of selected days for specific clinic
        morning_start = request.POST.get(f'morning_start_{clinic}')
        morning_end = request.POST.get(f'morning_end_{clinic}')
        afternoon_start = request.POST.get(f'afternoon_start_{clinic}')
        afternoon_end = request.POST.get(f'afternoon_end_{clinic}')
        
        try:
            if not isinstance(selected_days, list):
                selected_days = [selected_days]

            if morning_start > morning_end or afternoon_start > afternoon_end:
                print('Invalid Time Range')
                messages.error(request, 'Invalid Time Range')
                return redirect('AppointmentScheduling')

            # Save appointment schedule to Firebase
            data = {
                'uid': uid,
                'days': selected_days,
                'morning_start': str(morning_start),
                'morning_end': str(morning_end),
                'afternoon_start': str(afternoon_start),
                'afternoon_end': str(afternoon_end),
            }

            existing_schedules = db.child('appointmentschedule').child(uid).get().val()

            if existing_schedules:
                for schedule_id, existing_schedule in existing_schedules.items():
                    if clinic != schedule_id:
                        existing_days = existing_schedule['days']
                        existing_morning_start = existing_schedule['morning_start']
                        existing_morning_end = existing_schedule['morning_end']
                        existing_afternoon_start = existing_schedule['afternoon_start']
                        existing_afternoon_end = existing_schedule['afternoon_end']

                        for day in selected_days:
                            if day in existing_days:
                                print('Checking Conflict')
                                if morning_start and morning_end and existing_morning_start and existing_morning_end:
                                    if (morning_start < existing_morning_end and morning_end > existing_morning_start):
                                        print('Conflict Morning')
                                        messages.error(request, 'Conflicting Schedule with Another Clinic')
                                        return redirect('AppointmentScheduling')

                                 # Check for conflict in the afternoon schedule
                                if afternoon_start and afternoon_end and existing_afternoon_start and existing_afternoon_end:
                                    if (afternoon_start < existing_afternoon_end and afternoon_end > existing_afternoon_start):
                                       print('Conflict Afternoon')
                                       messages.error(request, 'Conflicting Schedule with Another Clinic')
                                       return redirect('AppointmentScheduling')
                                        
            db.child('appointmentschedule').child(uid).child(clinic).update(data)
            print('Appointment schedule saved successfully!')
            messages.success(request, 'Appointment schedule saved successfully!')
            return redirect('AppointmentScheduling')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    # Preprocess clinic schedules for the template
    preprocessed_clinic_schedules = []
    for clinic_id, schedule in clinic_schedules.items():
        preprocessed_clinic_schedules.append({
            'clinic_id': clinic_id,
            'selected_days': schedule['selected_days'],
            'morning_start': schedule['morning_start'],
            'morning_end': schedule['morning_end'],
            'afternoon_start': schedule['afternoon_start'],
            'afternoon_end': schedule['afternoon_end'],
        })
        
    return render(request, 'hmis/AppointmentScheduling.html', {
        'uid': uid, 
        'doctors': doctors, 
        'clinics': clinics, 
        'notifications': notifications, 
        'days_of_week': days_of_week, 
        'clinic_schedules': preprocessed_clinic_schedules,
        'found_clinic' : found_clinic
    })


def DoctorDashboard(request):
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    if request.session.get('uid') is None:
        return redirect('home')
    
    # Clear old messages
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them
    
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    submittedTest = db.child("submittedTest").get().val()
    appointments = db.child("appointments").get().val()
    clinics = db.child("clinics").get().val()
    patientsorders = db.child("patientsorders").get().val()
    prescriptionsorders = db.child("prescriptionsorders").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

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
                    if appointment_datetime >= date.datetime.now() and appointment_datetime < (date.datetime.now()+ timedelta(days=1)) and appointment_data["status"] == "Confirmed":
                        upcoming_appointments[appointment_id] = appointment_data     

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

    combined_data = []
    for patient_id, patient_data in chosenPatients.items():
        if patient_id in patientsdata:
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patient_id == appointment_data['patientName']:
                    patient_data['disease'] = patientsdata[patient_id].get('disease', 'Unknown Disease')
                    patient_data['lastVisited'] = patientsdata[patient_id].get('lastVisited', '2024-01-01')
            combined_data.append(patient_data)

    # Sort combined_data by lastVisited
    sorted_patients = sorted(combined_data, key=itemgetter('lastVisited'), reverse=True)
    adherence = defaultdict(list)
    dates = []
    if patients:
        for patient_data in sorted_patients:
            patients_id = patient_data.get('uid')
            if patients_id in patientsorders:
                latest_date_pres = max(patientsorders[patients_id].keys())
                adherence_percentages = {}
                date_data = patientsorders[patients_id][latest_date_pres]
                print(date_data)
                max_days_prescribed = 0
                
                for inside_id, inside_data in date_data.items():
                    medicine_name = inside_data['medicine_name']
                    dispensed = inside_data['days']
                    remaining = inside_data['total']
                    prescribed = inside_data['days']
                    days = inside_data['days']
                    dateCreated = inside_data['dateCreated']
                    presURL = inside_data['presURL']
                   # max_days_prescribed = max(entry['days'] for entry in date_data.values())
                    

                    adherence_percentage = ((dispensed - remaining) / ((prescribed / days) * days)) * 100
                    adherence_percentages.setdefault(medicine_name, []).append(adherence_percentage)

                    if days > max_days_prescribed:
                        max_days_prescribed = days
                    

                # Calculate average adherence percentage for each medicine_name
                for medicine_name, percentages in adherence_percentages.items():
                    average_adherence = sum(percentages) / len(percentages)
                    
                    adherence[patients_id].append({
                        'patientsorders_id': patients_id,
                        'medicine_name': medicine_name,
                        'average_adherence_percentage': average_adherence,
                        'dateCreated': dateCreated,
                        'max_days_prescribed': max_days_prescribed,
                        'presURL': presURL
                    })

                

                for patientsorders_id, adherence_data in adherence.items():
                    total_average = sum(entry['average_adherence_percentage'] for entry in adherence_data) / len(adherence_data)
                    total_average_rounded = round(total_average, 2)

                    if adherence_data:
                        date_created = adherence_data[0].get('dateCreated', None)
                        pres_URL = adherence_data[0].get('presURL', None)
                        max_days_prescribed = adherence_data[0].get('max_days_prescribed', None)

                        if date_created and max_days_prescribed:
                            date_created_dt = datetime.strptime(date_created, '%Y-%m-%d')
                            end_date = date_created_dt + timedelta(days=max_days_prescribed)
                            end_date_str = end_date.strftime('%Y-%m-%d')
                        else:
                            end_date_str = None
                    else:
                        date_created = None
                        pres_URL = None
                        max_days_prescribed = None
                        end_date_str = None

                    total_average_adherence[patientsorders_id] = {
                        'total_average_adherence': total_average_rounded,
                        'dateEnd': end_date_str,
                        'patientsorders_id': patientsorders_id,
                        'presURL': pres_URL
                    }
                
                # Iterate over total_average_adherence
                for patientsorders_id, adherence_data in total_average_adherence.items():
                    pres_URL = adherence_data['presURL']

                    # Iterate over prescriptionsorders
                    for patient_uid, prescriptions_data in prescriptionsorders.items():
                        for prescriptions_id, prescription_data in prescriptions_data.items():
                            if prescription_data.get('prescriptionURL') == pres_URL:
                                # Add doctor's UID to total_average_adherence
                                adherence_data['doctor_uid'] = prescription_data.get('doctor')
                
                #print(total_average_adherence)
                    
            
    # # Dictionary to hold latest prescription dates for each patient
    #     latest_prescriptions = {}
    #     for patientsorders_id, adherence_data in total_average_adherence.items():
    #         if adherence_data['doctor_uid'] == uid:
    #             latest_prescriptions[patientsorders_id] = adherence_data
        
    #     print(latest_prescriptions)

    # if prescriptionsorders:
    #     for patient_id, prescriptions in prescriptionsorders.items():
    #         # Find the latest prescription based on dateCreated
    #         latest_prescription = max(prescriptions.items(), key=lambda item: item[1]['dateCreated'])[1]
    #         latest_prescriptions[patient_id] = latest_prescription['dateCreated']

    return render(request, 'hmis/doctordashboard.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors,
                                                             'chosenPatientData': chosenPatientData,
                                                             'submittedTest':submittedTest,'patients1': chosenPatients,
                                                             'clinics': clinics,
                                                             'patientsorders': patientsorders,
                                                             'total_average_adherence': total_average_adherence,
                                                             'notifications': notifications,
                                                             'sorted_patients': sorted_patients,
                                                             }) 

def patient_data_doctor_view(request):
    # Fetch patients from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    appointments = db.child("appointments").get().val()
    doctors = db.child("doctors").get().val()
    clinics = db.child("clinics").get().val()
    uid = request.session['uid']
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    chosenPatients = {}
    if patients:
        for patients_id, patients_data in patients.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patients_id == appointment_data['patientName']:
                    chosenPatients[patients_id] = patients_data

    chosenPatientData = {}
    if patientsdata:
        for patientsdata_id, patientsdata_data in patientsdata.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patientsdata_id == appointment_data['patientName']:
                    chosenPatientData[patientsdata_id] = patientsdata_data

    combined_data = []
    for patient_id, patient_data in chosenPatients.items():
        if patient_id in patientsdata:
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patient_id == appointment_data['patientName']:
                    patient_data['disease'] = patientsdata[patient_id].get('disease', 'Unknown Disease')
                    patient_data['lastVisited'] = patientsdata[patient_id].get('lastVisited', '2024-01-01')
            combined_data.append(patient_data)

    # Sort combined_data by lastVisited
    sorted_patients = sorted(combined_data, key=itemgetter('lastVisited'), reverse=True)

    # Pass the patients data to the template
    return render(request, 'hmis/patient_data_doctor_view.html', {
        'patients': chosenPatients,
        'chosenPatientData': chosenPatientData,
        'doctors': doctors,
        'uid': uid,
        'appointments': appointments,
        'clinics': clinics,
        'sorted_patients': sorted_patients,
        'notifications': notifications
    }) 

def patient_personal_information_inpatient(request):
    
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them

    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    consulnotes = db.child("consultationNotes").get().val()
    progressnotes = db.child("progressnotes").get().val()
    

    patientsymptoms = db.child("symptoms").get().val()
    symptoms_list = db.child("symptomsList").get().val()

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
    clinics = db.child("clinics").get().val()
    uid = request.session['uid']   
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    time_slots = []
    list_final = []

    next_available_dates = []
    clinic_data_list = []
    days_checked = 0
    
    next_available_date = None
    current_date = datetime.now()
    next_available_date1 = None  # Initialize the variable to store the next available date
    doctors_data_list = []
    clinic_doctor_list = []
    chosenPatient = request.GET.get('chosenPatient', '')
    endAppointment = request.GET.get('appointmentID', '')

    clinic_doctor_list = get_clinic_doctor_list()

    clinic_schedule1 = db.child("appointmentschedule").child(uid).get().val()
    available_days = set()
    if clinic_schedule1:
        for clinic_id, clinic_data in clinic_schedule1.items():
            days = clinic_data.get('days', [])
            available_days.update(days)

    available_days_list = list(available_days)

    
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
                    if appointment_datetime >= date.datetime.now() and appointment_data["status"] == "Confirmed":
                        upcoming_appointments[appointment_id] = appointment_data

        # Sort appointments by date
        sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: date.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))
    else:
        sorted_upcoming_appointments = {}

    appointmentschedule_data1 = db.child("appointmentschedule").child(uid).get().val()
    
    for clinic_id, clinic_data in appointmentschedule_data1.items():
        time_slots1 = []
        for items_id, items_data in clinic_data.items():
            available_days_str1 = []
            if 'days' in items_id:
                for day_name in items_data:
                    available_days_str1.append(day_name.lower())
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
                    morning_start = datetime.strptime(clinic_data["morning_start"], '%H:%M')
                    morning_end = datetime.strptime(clinic_data["morning_end"], '%H:%M')
                    afternoon_start = datetime.strptime(clinic_data["afternoon_start"], '%H:%M')
                    afternoon_end = datetime.strptime(clinic_data["afternoon_end"], '%H:%M')
                    
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
    for clinic_id, clinic_data in appointmentschedule_data.items():
        time_slots = []
        for items_id, items_data in clinic_data.items():
            

            available_days_str = []
            if 'days' in items_id:
                for day_name in items_data:
                    available_days_str.append(day_name.lower())
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

                    # Define time slots for morning
                    morning_start_str = clinic_data["morning_start"]
                    morning_end_str = clinic_data["morning_end"]

                    # Convert strings to datetime objects for morning
                    morning_start = datetime.strptime(morning_start_str, '%H:%M')
                    morning_end = datetime.strptime(morning_end_str, '%H:%M')

                    # Define time slots for afternoon
                    afternoon_start_str = clinic_data["afternoon_start"]
                    afternoon_end_str = clinic_data["afternoon_end"]

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
                else:
                    print("No time slots available")

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

    #Get Patient Symptoms
    chosenPatientSymptoms = {}
    for patientsymptoms_id, patientsymptoms_data in patientsymptoms.items():
        if patientsymptoms_id == chosenPatient:
            chosenPatientSymptoms[patientsymptoms_id] = patientsymptoms_data

    chosenPatientSymptoms1 = []

    if chosenPatient in patientsymptoms:
        patient_data1 = patientsymptoms[chosenPatient]
        for symptom, details in patient_data1.items():
            formatted_symptom = symptom.replace('_', ' ')
            chosenPatientSymptoms1.append(formatted_symptom)


    print(chosenPatientSymptoms1)
    print(chosenPatientSymptoms1)


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
        for clinic_id, clinic_data in appointmentschedule_data.items():
    # Define time slots for morning
            morning_start_str = clinic_data["morning_start"]
            morning_end_str = clinic_data["morning_end"]

            # Convert strings to datetime objects for morning
            morning_start = datetime.strptime(morning_start_str, '%H:%M')
            morning_end = datetime.strptime(morning_end_str, '%H:%M')

            # Define time slots for afternoon
            afternoon_start_str = clinic_data["afternoon_start"]
            afternoon_end_str = clinic_data["afternoon_end"]

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

        if 'endingAppointment' in request.POST:
            endingAppointment = request.POST.get('endingAppointment')
            db.child("appointments").child(endingAppointment).update({'status': 'Finished'})
            print('endingAppointment', endingAppointment)

        if 'complaintButton' in request.POST:
            save_chiefComplaint(request)

        if 'confirmReferral' in request.POST:
            confirmReferral = request.POST.get('confirmReferral')

            data = {
                'patientUID': chosenPatient,
                'referringDoctor': uid,
                'referredDoctor': request.POST.get('doctors_listahan'),
                'referredClinic': request.POST.get('clinic_referring'),
                'status': 'Pending'
            }

            db.child('referralRequest').child(chosenPatient).push(data)
            messages.success(request, f'Patient successfully referred to {data["referredDoctor"]}')

        if 'submitMedOrder' in request.POST:
            patient_uid = request.GET.get('chosenPatient')
            patientdata = db.child("patientdata").child(patient_uid).get().val()
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
 
    
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    consulnotes = db.child("consultationNotes").get().val()
    date1 = datetime.today().strftime('%Y-%m-%d')
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 

    chosenPatient = request.GET.get('chosenPatient', '')

    appointmentschedule = db.child("appointmentschedule").get().val()
    shortnessOfBreathInput = request.POST.get('shortnessOfBreathInput')
    coughInput = request.POST.get('coughInput')
    phlegmInput = request.POST.get('phlegmInput')
    wheezingInput = request.POST.get('wheezingInput')
    coughingBloodInput = request.POST.get('coughingBloodInput')
    chestPainInput = request.POST.get('chestPainInput')
    feverInput = request.POST.get('feverInput')
    heartMurmurInput = request.POST.get('heartMurmurInput')
    othersInput = request.POST.get('othersInput')

    today_date = datetime.now().strftime('%Y-%m-%d')
    todays_complaints = {}
    showOthers = {}
    today_data = []
    dates={}

    # for consultation_id, data in consulnotes.items():
    #     if consultation_id == chosenPatient:
    #         for id, dates in data.items():
    #             if id == today_date:
    #                 if 'complains' in dates:  
    #                     for key, value in dates['complains'].items():  
    #                         print('complains id are ', key)
    #                         print('complains value are ', value)
    #                 else:
    #                     print("No 'complains' found for this date.")

    for consultation_id, data in consulnotes.items():
        if consultation_id == chosenPatient:
            for id, dates_in_data in data.items():
                if id == today_date:
                    dates = dates_in_data  # Assign dates if the condition is met
                    if 'complains' in dates_in_data:  
                        for key, value in dates_in_data['complains'].items():  
                            dates = dates_in_data['complains']
                            print('complains id are ', key)
                            print('complains value are ', value)
                    else:
                        print("No 'complains' found for this date.")
                    break  # Exit the loop if the date is found
            if id == today_date:
                break  # Exit the outer loop if the patient is found

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

    
    first_appointment = next(iter(sorted_appointments.values()), None)
    first_appointment_date = first_appointment['appointmentDate'] if first_appointment else None
    if first_appointment_date is None:
        num_days = 0
    else:
        given_date = datetime.strptime(first_appointment_date, '%Y-%m-%d')
        today_date = datetime.now()
        num_days = (today_date - given_date).days

    prescriptionsorders = db.child("prescriptionsorders").get().val()
    # latest_prescription_url = None
    # latest_date = datetime.min

    # for prescription_id, prescription_data in prescriptionsorders.items():
    #     if prescription_id == chosenPatient:
    #         for id, data in prescription_data.items():
    #             date_created = datetime.strptime(data['dateCreated'], '%Y-%m-%d')
    #             if date_created > latest_date:
    #                 latest_date = date_created
    #                 latest_prescription_url = data['prescriptionURL']

        

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
                                                                                'disease_list': disease_list,
                                                                                'chosenPatientSymptoms': chosenPatientSymptoms,
                                                                             'symptoms_list': symptoms_list,
                                                                                'notifications': notifications,
                                                                                'clinics': clinics,
                                                                                'upcomings': upcomings,
                                                                                'doctors': doctors,
                                                                                'doctors_data_list': doctors_data_list,
                                                                                'appointmentIDurl': endAppointment,
                                                                                'clinic_doctor_list': clinic_doctor_list,
                                                                                'chosenPatient': chosenPatient,
                                                                                'chosenPatientSymptoms1': chosenPatientSymptoms1,
                                                                                'todays_complaints': todays_complaints,
                                                                                'showOthers': showOthers,
                                                                                'prescriptionsorders': prescriptionsorders,
                                                                                # 'latest_prescription_url': latest_prescription_url,
                                                                                'dates': dates,
                                                                                'available_days_list': available_days_list})

def save_chiefComplaint(request):
        
    date = datetime.today().strftime('%Y-%m-%d')
    # chiefComplaint = request.POST.get('chiefComplaint')
    id = request.POST.get('complaintButton') 
    uid = request.session['uid'] 
    
    # Save Chief Compliant into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

    # Update appointment data in Firebase
    if id:
        complains = {
            'shortnessOfBreathInput': request.POST.get('shortnessOfBreathInput'),
            'coughInput': request.POST.get('coughInput'),
            'phlegmInput': request.POST.get('phlegmInput'),
            'wheezingInput': request.POST.get('wheezingInput'),
            'coughingBloodInput': request.POST.get('coughingBloodInput'),
            'chestPainInput': request.POST.get('chestPainInput'),
            'feverInput': request.POST.get('feverInput'),
            'heartMurmurInput': request.POST.get('heartMurmurInput'),
            'othersInput': request.POST.get('othersInput'),
        }
        db.child(appointment_path).update({
            'patientID': id,
            'doctorID': uid,
            'complains': complains
        })
    
    messages.success(request, 'Consultation notes successfully saved')
    
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
    otherdiagnosis = request.POST.get('otherdiagnosis')
    id = request.POST.get('diagnosisButton') 
    uid = request.session['uid']

    print(diagnosis)
    print(otherdiagnosis)

    
    # Save Chief Compliant into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure
    appointment_path1 = f"/patientdata/{id}"  # Adjust the path as per your Firebase structure
    
    # Update appointment data in Firebase
    if diagnosis != 'Other' and diagnosis:
        db.child(appointment_path).update({
            'patientID': id,
            'doctorID': uid,
            'diagnosis': diagnosis
        })

        db.child(appointment_path1).update({
            'disease': diagnosis
        })
    elif diagnosis == 'Other' and otherdiagnosis:
        db.child(appointment_path).update({
            'patientID': id,
            'doctorID': uid,
            'diagnosis': otherdiagnosis
        })

        db.child(appointment_path1).update({
            'disease': otherdiagnosis
        })
    
    messages.success(request, 'Diagnosis Successfully Saved')
    
#Calculate age function for retrieving patient data

def calculate_age(birthday):
    today = datetime.today()
    birthdate = datetime.strptime(birthday, '%Y-%m-%d').date()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def calculate_copd_risk(baseline_risk, odds_ratio, num_family_members, smoking_factor):
    # Convert odds ratio to cumulative odds ratio
    cumulative_or = odds_ratio ** num_family_members
    
    # Adjust for smoking factor
    adjusted_or = cumulative_or * smoking_factor
    
    # Calculate adjusted probability
    final_probability = (baseline_risk * adjusted_or) / (1 + (baseline_risk * (adjusted_or - 1)))
    
    return final_probability


def patient_medical_history(request):
    doctors = db.child("doctors").get().val()
    patientsdata = db.child("patients").get().val()
    appointments = db.child("appointments").get().val()
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    consulNotes = db.child("consultationNotes").get().val()
    testrequest = db.child("testrequest").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    prescriptionsorders = db.child("prescriptionorders").get().val()
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid).get().val()

    # Filter prescriptions to include only those prescribed by the logged-in doctor
    doctor_prescriptions = {}
    for prescription_id, prescription_data in prescriptionsorders_ref.items():
        if prescription_data.get('doctor') == uid:
            doctor_prescriptions[prescription_id] = prescription_data
    
    print(doctor_prescriptions)

    patientMedical = db.child("patientmedicalhistory").get().val()

    copd = ['chronic Bronchitis', 'emphysema', 'copd', 'chronic obstructive pulmonary disease']
    baseline_risk = 0.14
    odds_ratio = 1.57

    num_family_members_with_copd = 0

    # Iterate through the patient medical data
    for medical_id, medical_data in patientMedical.items():
        if medical_id == chosenPatient:
            for m_id, m_data in medical_data.items():
                if m_id == 'familyHistory':
                    for f_id, f_data in m_data.items():
                        # Check if any COPD-related diagnosis is in f_data['diagnosis']
                        if any(copd_diagnosis.lower() in f_data['diagnosis'].lower() for copd_diagnosis in copd):
                            num_family_members_with_copd += 1
                if m_id == 'socialHistory':   
                    smoking_status = m_data['smokingStatus'].lower()
                    if smoking_status == 'current smoker':
                        smoking_factor = 1.46  # Higher risk factor for current smokers
                    elif smoking_status == 'former smoker':
                        smoking_factor = 1.21  # Lower risk factor for former smokers
                    elif smoking_status == 'not at all':
                        smoking_factor = 1.0 
                        


    # Calculate COPD risk
    copd_risk = round((calculate_copd_risk(baseline_risk, odds_ratio, num_family_members_with_copd, smoking_factor))*100, 2)

    chosenPatientData= {}
    
    if patientsdata:
        for patientsdata_id, patientsdata_data in patientsdata.items():
            for appointment_id, appointment_data in appointments.items():
                if appointment_data['doctorUID'] == uid and patientsdata_id == appointment_data['patientName']:
                    chosenPatientData[patientsdata_id] = patientsdata_data

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
            data = {
                'patient_id': chosen_patient_uid,
                'smoking': smoking,
                'yearsSmoking': yearsSmoking
                #'alcohol': alcohol
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('socialHistory').update(data)

    def transform_symptom_name(symptom):
        parts = symptom.replace('Input', '').split('_')
        transformed_parts = []
        
        for part in parts:
            temp_parts = []
            
            for i, char in enumerate(part):
                if char.isupper() and i > 0:
                    temp_parts.append(' ')
                temp_parts.append(char)
            
            transformed_parts.append(''.join(temp_parts))
        return ' '.join(transformed_parts).capitalize()

    symptom_counter = defaultdict(int)

    for patient_id, dates in consulNotes.items():
        if patient_id == chosenPatient:
            for date, data in dates.items():
                if 'complains' in data and data['doctorID'] == uid:
                    for symptom, description in data['complains'].items():
                        transformed_symptom = transform_symptom_name(symptom)
                        symptom_counter[transformed_symptom] += 1

    sorted_symptoms = sorted(symptom_counter.items(), key=lambda item: item[1], reverse=True)

    # Step 4: Get the top 3 most recurring symptoms and their total numbers
    top_3_symptoms = sorted_symptoms[:3]


    return render(request, 'hmis/patient_medical_history.html', {'doctors': doctors,
                                                                 'uid': uid,
                                                                 'patientMedical': patientMedical,
                                                                 'chosenPatient': chosenPatient,
                                                                 'consulNotes': consulNotes,
                                                                 'prescriptionsorders': prescriptionsorders,
                                                                 'prescriptionsorders_ref': prescriptionsorders_ref,
                                                                 'testrequest': testrequest,
                                                                 'notifications': notifications,
                                                                 'chosenPatientData': chosenPatientData,
                                                                 'copd_risk': copd_risk, 
                                                                 'top_3_symptoms': top_3_symptoms})

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
    
    # Get the latest date
    latest_date = sorted_dates[0] if sorted_dates else None

    chosenPatientTreatmentPlan = {}
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = prescriptionsorders_ref.child(latest_date).get().val()
    if consulnotes_data:
        chosenPatientTreatmentPlan[chosen_patient_uid] = consulnotes_data
    
    return render(request, 'hmis/view_treatment_plan.html', {
        'chosen_patient_uid': chosen_patient_uid,
        'patients': patients,
        'prescriptionsorders': chosenPatientTreatmentPlan,
        'latest_date': latest_date,
        'doctors': doctors,
        'uid': uid
    })

def patient_medication_doctor(request):
    # Fetch patients data from Firebase
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    uid = request.session['uid'] 
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    # Pass the combined data to the template
    return render(request, 'hmis/patient_medication_doctor.html', {'patients': patients, 'patientsdata': patientsdata, 'notifications': notifications})

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

def pharmacy_drugs(request):
    #collection = connect_to_mongodb()
    cursor = collection.find().limit(10)

    # Convert the cursor to a list of dictionaries
    data = list(cursor)

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
    disease = request.GET.get('diagnosis')
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    todaydate = datetime.now().strftime("%Y-%m-%d")
    clinics = db.child("clinics").get().val()

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patient_age = calculate_age(patients_data["bday"])
            patients_data["age"] = patient_age
            patientData[patients_id] = patients_data


    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 
                                                                     'medicines_list': medicines_list, 
                                                                     'pharmacy_lists':pharmacy_lists_json,
                                                                     'patient_uid': patient_uid,
                                                                     'doctors': doctors,
                                                                     'uid': uid,
                                                                     'todaydate': todaydate,
                                                                     'clinics' :clinics, 
                                                                     'patientData': patientData,
                                                                     'disease': disease,
                                                                     'notifications': notifications})

@csrf_exempt
def save_prescriptions(request):
    patient_uid = request.GET.get('chosenPatient')
    patients = db.child("patients").get().val()
    todaydate = datetime.now().strftime("%Y-%m-%d")
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 
    clinics = db.child("clinics").get().val()

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patient_age = calculate_age(patients_data["bday"])
            patients_data["age"] = patient_age
            patientData[patients_id] = patients_data


    patientName = patientData[patient_uid].get('fname','N/A') + ' ' + patientData[patient_uid].get('lname','N/A')
    patientGender = patientData[patient_uid].get('gender','N/A')
    patientAddress = patientData[patient_uid].get('address','N/A')
    patientAge = patientData[patient_uid].get('age','N/A')
    numClinics = 0
    doctor_clinics = []

    for doctor_id, doctor_data in doctors.items():
        if uid == doctor_data["uid"]:
            doctorName = doctor_data["fname"] + ' ' + doctor_data["lname"]
            specialization = doctor_data['specialization']
            license = str(doctor_data["license"])
            ptr = str(doctor_data["ptr"])
            doctor_uid = doctor_id
            for clinic_id in doctor_data["clinic"]:
                if clinic_id in clinics:
                    numClinics+=1
                    clinic_info = clinics[clinic_id]
                    doctor_clinics.append(clinic_info)


    # Generate unique ID for the prescription
    prescription_id = str(uuid.uuid1())

    data = {
        'patient_name': patientName,
        'patient_age': patientAge,
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
        'numClinics': numClinics,
        'clinics': doctor_clinics
    }

    # Construct the path to the appointment data in Firebase
    db_path = f"/prescriptionsorders/{patient_uid}/{prescription_id}"
    db_path2 = f"/patientsorders/{patient_uid}/"

    db.child(db_path).update( {
        'patient_id': patient_uid,
        'doctor': doctor_uid,
        'dateCreated': todaydate,
        'medicines': {
            'name': request.POST.getlist('medicine_name'),
            'dosage': request.POST.getlist('dosage'),
            'route': request.POST.getlist('route'),
            'times': request.POST.getlist('times'),
            'days': request.POST.getlist('days'),
        },
        'status': "Ongoing",
    })

     # Handle file upload
    signature = request.FILES.get('signature')
    #print(signature)
    signature_path = None
    if signature:
        signature_path = 'static/signature.png'
        with open(signature_path, 'wb+') as destination:
            for chunk in signature.chunks():
                destination.write(chunk)

    # Create the PDF
    temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_prescription.pdf')
    create_prescription_pdf(data, temp_file_path, signature_path)

    try:
        # Upload the PDF to Firebase
        storage_path = patient_uid + '/prescriptions/' + todaydate +'-prescription.pdf'
        upload_pdf_to_firebase(temp_file_path, storage_path)

        pdf_url = firebase_storage.child(f"{storage_path}").get_url(None)
        print("PDF Download URL: ", pdf_url)

        db.child(db_path).update( {
            'prescriptionURL': pdf_url,
        })

        medicines = data['medicines']
        for i in range(len(medicines['name'])):
            endDate = datetime.strptime(todaydate, '%Y-%m-%d') + timedelta(days=int(medicines['days'][i]))
            endDate_str = endDate.strftime('%Y-%m-%d')
            medicine_data = {
                'dateCreated': todaydate,
                'endDate': endDate_str,
                'dosage': medicines['dosage'][i],
                'medicine_name': medicines['name'][i],
                'route': medicines['route'][i],
                'times': medicines['times'][i],
                'counter': int(medicines['days'][i]),
                'days': int(medicines['days'][i]),
                'total': int(medicines['days'][i]),
                'status': "Ongoing",
                'presURL': pdf_url,
            }

            print(medicine_data)

            # Interpret times and split accordingly
            times = medicines['times'][i].split('-')
            time_periods = ['Breakfast', 'Lunch', 'Dinner']

            print(medicine_data)

            for j, time in enumerate(times):
                if time == '1':
                    specific_time_data = medicine_data.copy()
                    specific_time_data['times'] = time_periods[j]
                    # Generate a unique ID for each entry in patientsorders
                    per_id = str(uuid.uuid1())
                    db.child(db_path2).child(todaydate).child(per_id).update(specific_time_data)
            
        # Success message
        messages.success(request, 'Prescriptions created successfully.')           
        return redirect(reverse('patient_personal_information_inpatient') + f'?chosenPatient={patient_uid}')
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect(reverse('outpatient_medication_order') + f'?chosenPatient={patient_uid}')
    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if signature_path and os.path.exists(signature_path):
            os.remove(signature_path)

def diagnostic_imagery_reports(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    submittedTest = db.child("submittedTest").get().val()
    doctors = db.child("doctors").get().val()
    patients = db.child("patients").get().val()
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    testRequests = db.child("testrequest").get().val()
                
    
    return render(request, 'hmis/diagnostic_imagery_reports.html', {'patients': patients,'testRequest': testRequests,'submittedTest': submittedTest, 'chosenPatient': chosenPatient, 'doctors': doctors, 'uid': uid})

def diagnostic_reports(request):
    submittedTest = db.child("submittedTest").get().val()
    doctors = db.child("doctors").get().val()
    patients = db.child("patients").get().val()
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    testRequests = db.child("testrequest").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    
    return render(request, 'hmis/diagnostic_imagery_reports.html', {'patients': patients,
                                                                    'testRequest': testRequests,
                                                                    'submittedTest': submittedTest, 
                                                                    'chosenPatient': chosenPatient, 
                                                                    'doctors': doctors, 
                                                                    'uid': uid,
                                                                    'notifications': notifications})

def download_image(url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    return None

def create_prescription_pdf(data, filename, signature_path=None):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Set the margins
    margin = 0.5 * inch

    # Draw header
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - margin - 0.5 * inch, data['doctor'] + ", M.D.")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - margin - 0.8 * inch, data['specialization'])
    if data['numClinics'] == 1:
        for clinic in data['clinics']:
            c.setFont("Helvetica", 12)
            # Draw clinic name
            c.drawCentredString(width / 2, height - margin - 1.1 * inch, clinic['name'])
            # Draw clinic address below the name
            c.drawCentredString(width / 2, height - margin - 1.3 * inch, clinic['address'])
            # Draw clinic address below the name
            c.drawCentredString(width / 2, height - margin - 1.5 * inch, clinic['onumber'])
    elif data['numClinics'] == 2:
        left_x = width / 4  # Position for the left clinic
        right_x = 3 * width / 4  # Position for the right clinic
        
        for i, clinic in enumerate(data['clinics']):
            c.setFont("Helvetica", 12)
            
            if i == 0:
                # Draw the first clinic on the left side
                c.drawCentredString(left_x, height - margin - 1.1 * inch, clinic['name'])
                c.drawCentredString(left_x, height - margin - 1.3 * inch, clinic['address'])
                c.drawCentredString(left_x, height - margin - 1.5 * inch, clinic['onumber'])
            elif i == 1:
                # Draw the second clinic on the right side
                c.drawCentredString(right_x, height - margin - 1.1 * inch, clinic['name'])
                c.drawCentredString(right_x, height - margin - 1.3 * inch, clinic['address'])
                c.drawCentredString(right_x, height - margin - 1.5 * inch, clinic['onumber'])
    elif data['numClinics'] == 3:
        positions = [width / 4, width / 2, 3 * width / 4]  # Positions for three clinics
        
        for i, clinic in enumerate(data['clinics']):
            c.setFont("Helvetica", 12)
            
            # Draw each clinic at its respective position
            c.drawCentredString(positions[i], height - margin - 1.1 * inch, clinic['name'])
            c.drawCentredString(positions[i], height - margin - 1.3 * inch, clinic['address'])
            c.drawCentredString(positions[i], height - margin - 1.5 * inch, clinic['onumber'])



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
    c.drawString(3.5 * inch + 1.0 * inch, patient_info_y, str(data['patient_age']))
    
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
        y_position -= 0.2 * inch
        c.drawString(indent, y_position, f"Dosage: {dosage}")
        c.drawString(indent + 1.5 * inch, y_position, f"Route: {route}")
        y_position -= 0.2 * inch
        c.drawString(indent, y_position, f"Times: {times}")
        c.drawString(indent + 1.5 * inch, y_position, f"Days: {days}")
        y_position -= 0.4 * inch  # Extra space between different medicines

    # Add two break lines before the footer
    y_position -= 0.6 * inch

    # Draw footer (right-aligned)
    footer_text = [
        "Doctor's Signature: ",
        "License No.: " + data['license'],
        "PTR No.: " +  data['ptr'],
    ]
    # Draw the signature text and image
    c.setFont("Helvetica", 12)
    c.drawRightString(width - margin - 2.0 * inch, y_position, footer_text[0])
    if signature_path and os.path.exists(signature_path):
        signature_width = 1.8 * inch
        signature_height = 0.5 * inch
        c.drawImage(signature_path, width - margin - signature_width, y_position - signature_height + 15, width=signature_width, height=signature_height, mask='auto')
    
    for i, text in enumerate(footer_text[1:]):
        c.setFont("Helvetica", 12)
        c.drawRightString(width - margin - 2.05 * inch, y_position - (i + 1) * 0.3 * inch, text)

    c.showPage()
    c.save()

def upload_pdf_to_firebase(file_path, storage_path):
    firebase_storage.child(storage_path).put(file_path)

@csrf_exempt
def requestTest(request):
     # Clear old messages
    for message in messages.get_messages(request):
        pass  # Iterating over the messages clears them

    patient_uid = request.GET.get('chosenPatient')
    patients = db.child("patients").get().val()
    todaydate = datetime.now().strftime("%Y-%m-%d")
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 
    clinics = db.child("clinics").get().val()
    notifications = Notification.objects.filter(firebase_id=uid, is_read=False)

    patientData = {}
    for patients_id, patients_data in patients.items():
        if patient_uid == patients_data["uid"]:
            patient_age = calculate_age(patients_data["bday"])
            patients_data["age"] = patient_age
            patientData[patients_id] = patients_data

    patientName = patientData[patient_uid].get('fname','N/A') + ' ' + patientData[patient_uid].get('lname','N/A')
    patientGender = patientData[patient_uid].get('gender','N/A')
    patientAddress = patientData[patient_uid].get('address','N/A')
    patientAge = patientData[patient_uid].get('age','N/A')
    numClinics = 0
    doctor_clinics = []

    for doctor_id, doctor_data in doctors.items():
        if uid == doctor_data["uid"]:
            doctorName = doctor_data["fname"] + ' ' + doctor_data["lname"]
            specialization = doctor_data['specialization']
            license = str(doctor_data["license"])
            ptr = str(doctor_data["ptr"])
            doctor_uid = doctor_id
            for clinic_id in doctor_data["clinic"]:
                if clinic_id in clinics:
                    numClinics+=1
                    clinic_info = clinics[clinic_id]
                    doctor_clinics.append(clinic_info)


    if request.method == 'POST':
        # Generate unique ID for the prescription
        testRequest_id = str(uuid.uuid1())

        data = {
            'patient_name': patientName,
            'patient_age': patientAge,
            'patient_gender': patientGender,
            'patient_address': patientAddress,
            'date': todaydate,
            'tests': request.POST.getlist('test'),
            'doctor': doctorName,
            'specialization':specialization,
            'license': license,
            'ptr': ptr,
            'numClinics': numClinics,
            'clinics': doctor_clinics
        }

        # Construct the path to the appointment data in Firebase
        db_path = f"/testrequest/{patient_uid}/{testRequest_id}"

        db.child(db_path).update( {
            'patient_id': patient_uid,
            'doctor': doctor_uid,
            'dateCreated': todaydate,
            'tests': request.POST.getlist('test'),
            'status': "Ongoing",
        })


        # Handle file upload
        signature = request.FILES.get('signature')
        print(signature)
        signature_path = None
        if signature:
            signature_path = 'static/signature.png'
            with open(signature_path, 'wb+') as destination:
                for chunk in signature.chunks():
                    destination.write(chunk)

        # Create the PDF
        temp_file_path = os.path.join(os.path.dirname(__file__), 'temp_prescription.pdf')
        create_tests_pdf(data, temp_file_path, signature_path)

        try:
            # Upload the PDF to Firebase
            storage_path = patient_uid + '/testRequests/' + todaydate +'-testRequests.pdf'
            upload_pdf_to_firebase(temp_file_path, storage_path)

            pdf_url = firebase_storage.child(f"{storage_path}").get_url(None)
            print("PDF Download URL: ", pdf_url)

            db.child(db_path).update( {
                'testURL': pdf_url,
            })

            # Success message
            messages.success(request, 'Test request created successfully.')
            return redirect(reverse('patient_personal_information_inpatient') + f'?chosenPatient={patient_uid}')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect(reverse('requestTest') + f'?chosenPatient={patient_uid}')
        finally:
            # Ensure the temporary file is deleted
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if signature_path and os.path.exists(signature_path):
                os.remove(signature_path)

    return render(request, 'hmis/requestTest.html' , {'patientData': patientData,
                                                        'patient_uid': patient_uid,
                                                        'doctors': doctors,
                                                        'clinics': clinics,
                                                        'uid': uid,
                                                        'todaydate': todaydate,
                                                        'notifications': notifications})

def create_tests_pdf(data, filename, signature_path=None):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Set the margins
    margin = 0.5 * inch

    # Draw header
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - margin - 0.5 * inch, data['doctor'] + ", M.D.")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - margin - 0.8 * inch, data['specialization'])
    if data['numClinics'] == 1:
        for clinic in data['clinics']:
            c.setFont("Helvetica", 12)
            # Draw clinic name
            c.drawCentredString(width / 2, height - margin - 1.1 * inch, clinic['name'])
            # Draw clinic address below the name
            c.drawCentredString(width / 2, height - margin - 1.3 * inch, clinic['address'])
            # Draw clinic address below the name
            c.drawCentredString(width / 2, height - margin - 1.5 * inch, clinic['onumber'])
    elif data['numClinics'] == 2:
        left_x = width / 4  # Position for the left clinic
        right_x = 3 * width / 4  # Position for the right clinic
        
        for i, clinic in enumerate(data['clinics']):
            c.setFont("Helvetica", 12)
            
            if i == 0:
                # Draw the first clinic on the left side
                c.drawCentredString(left_x, height - margin - 1.1 * inch, clinic['name'])
                c.drawCentredString(left_x, height - margin - 1.3 * inch, clinic['address'])
                c.drawCentredString(left_x, height - margin - 1.5 * inch, clinic['onumber'])
            elif i == 1:
                # Draw the second clinic on the right side
                c.drawCentredString(right_x, height - margin - 1.1 * inch, clinic['name'])
                c.drawCentredString(right_x, height - margin - 1.3 * inch, clinic['address'])
                c.drawCentredString(right_x, height - margin - 1.5 * inch, clinic['onumber'])
    elif data['numClinics'] == 3:
        positions = [width / 4, width / 2, 3 * width / 4]  # Positions for three clinics
        
        for i, clinic in enumerate(data['clinics']):
            c.setFont("Helvetica", 12)
            
            # Draw each clinic at its respective position
            c.drawCentredString(positions[i], height - margin - 1.1 * inch, clinic['name'])
            c.drawCentredString(positions[i], height - margin - 1.3 * inch, clinic['address'])
            c.drawCentredString(positions[i], height - margin - 1.5 * inch, clinic['onumber'])


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
    c.drawString(3.5 * inch + 1.0 * inch, patient_info_y, str(data['patient_age']))
    
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

    # Draw test details
    y_position = height - 4.0 * inch
    indent = margin + 2.0 * inch
    c.setFont("Helvetica", 13)
    c.drawString(indent , y_position, "Request for:")
    y_position -= 0.2 * inch
    for test in data['tests']:
        c.setFont("Helvetica", 13)
        c.drawString(indent + 1.25 * inch, y_position, test)
        y_position -= 0.3 * inch  # Extra space between different medicines

    # Add two break lines before the footer
    y_position -= 0.6 * inch

    # Draw footer (right-aligned)
    footer_text = [
        "Doctor's Signature: ",
        "License No.: " + data['license'],
        "PTR No.: " +  data['ptr'],
    ]
    # Draw the signature text and image
    c.setFont("Helvetica", 12)
    c.drawRightString(width - margin - 2.0 * inch, y_position, footer_text[0])
    if signature_path and os.path.exists(signature_path):
        signature_width = 1.8 * inch
        signature_height = 0.5 * inch
        c.drawImage(signature_path, width - margin - signature_width, y_position - signature_height + 15, width=signature_width, height=signature_height, mask='auto')
    
    for i, text in enumerate(footer_text[1:]):
        c.setFont("Helvetica", 12)
        c.drawRightString(width - margin - 2.05 * inch, y_position - (i + 1) * 0.3 * inch, text)

    c.showPage()
    c.save()