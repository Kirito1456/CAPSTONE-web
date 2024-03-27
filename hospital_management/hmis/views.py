from datetime import datetime , timedelta
import datetime as date
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
            print(request.session['uid'])

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

        # Convert available days to numbers
        available_days_numbers = [day_name_to_number[day.lower()] for day in available_days_str if day.lower() in day_name_to_number]
        
        current_day_of_week = datetime.now().weekday()
        current_date = datetime.now()
        while len(next_available_dates) < 3 and days_checked < 7:  # Check up to 7 days
            if current_day_of_week in available_days_numbers:
                if current_date.date() not in [datetime.strptime(appointment_data['appointmentDate'], "%Y-%m-%d").date() for appointment_data in upcoming_appointments.values()]:
                    next_available_dates.append(current_date.date())
            current_date += timedelta(days=1)
            current_day_of_week = (current_day_of_week + 1) % 7
            days_checked += 1

        dates_to_pass = []
        for date_str in next_available_dates:
            dates_to_pass.append(date_str.strftime("%Y-%m-%d"))
            

    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentUpcoming.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors, 'time_slots': time_slots,
                                                             'next_available_dates': dates_to_pass})


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

def update_appointment(request):
    
    if request.method == 'POST':
        try:
            appID = request.POST.get('appID')
            #print('APPID', appID)

            new_time = request.POST.get('new_appointment_time')
            print('Time nakuha is ', new_time)

            # Assuming new_date_str is obtained from request.POST.get
            new_date_str = request.POST.get('selected_appointment_date')
            print(new_date_str)
            # Convert new_date_str to datetime object
            # new_date = datetime.strptime(new_date_str, "%B %d, %Y")
            # print(new_date)
            # # Format new_date to "YYYY-MM-DD" string
            # new_date_formatted = new_date.strftime("%Y-%m-%d")
            
            
            # print(new_date_formatted)

            # # Format time and date objects to desired format
            # new_time_formatted = date.datetime.strptime(new_time, "%H:%M")
            # new_time_str = new_time_formatted.strftime("%I:%M %p")
            # print(new_time_str)

            # Construct the path to the appointment data in Firebase
            appointment_path = f"/appointments/{appID}"  # Adjust the path as per your Firebase structure

            # Update appointment data in Firebase
            db.child(appointment_path).update({
                'appointmentDate': new_date_str,
                #'appointmentTime': new_time_str,
                'status': 'Ongoing',
            }) 
        

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('AppointmentUpcoming')  # Redirect to the appointments list page

    # Handle GET request or invalid form submission
    return redirect('AppointmentUpcoming')

def followup_appointment(request):
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    appointmentschedule = db.child("appointmentschedule").get().val()
    print('DLLOW1')
    
    if request.method == 'POST':
        print('DLL2')
        # try:
        print('DLLOW333')
        id=str(uuid.uuid1())
        endAppointment = request.POST.get('past-appointment-id')
        print(endAppointment)
        appID = request.POST.get('appID')
        # Get the date from the request.POST dictionary
        date_str = request.POST.get('three_days_after')

        # Convert the date string to a datetime object
        date_obj = datetime.strptime(date_str, '%B %d, %Y')

        # Format the datetime object to the desired format (yyyy-mm-dd)
        formatted_date = date_obj.strftime('%Y-%m-%d')

        new_time = request.POST.get('followup_time')
        doctor = request.session['uid']

        # Convert to datetime object
        time_obj = datetime.strptime(new_time, "%H:%M")

        # Convert to 12-hour format with AM/PM
        time_12h = time_obj.strftime("%I:%M %p")

        # Construct the path to the appointment data in Firebase
        appointment_path = f"/appointments/{id}"  # Adjust the path as per your Firebase structure

        # Update appointment data in Firebase
        # db.child(appointment_path).set({
        #     'doctorUID': doctor,
        #     'appointmentVisitType': "Follow-Up Visit",
        #     'appointmentDate': formatted_date,
        #     'appointmentTime': time_12h,
        #     'status': 'Ongoing',
        #     'patientName': appID
        # }) 
        data = {
            'doctorUID': doctor,
            'appointmentVisitType': "Follow-Up Visit",
            'appointmentDate': formatted_date,
            'appointmentTime': time_12h,
            'status': 'Ongoing',
            'patientName': chosenPatient
        }
        db.child("appointments").child(id).set(data)
        db.child("appointments").child(appID).update({'status': 'Finished'})

        # except Exception as e:
        #     messages.error(request, f'An error occurred: {str(e)}')

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
    
    return render(request, 'hmis/AppointmentCalendar.html', {'uid': uid, 'doctors': doctors, 'task_json': task_json})


def Message(request):
    return render(request, 'hmis/Message.html')

def AppointmentCalendarRequestDetails(request):
    return render(request, 'hmis/AppointmentCalendarRequestDetails.html')

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
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    rooms = db.child("rooms").get().val()

    # Filter and sort upcoming appointments
    upcoming_appointments = {}
    inpatients = {}
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

    


    # Pass the combined data to the template
    return render(request, 'hmis/doctordashboard.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors,
                                                             'inpatients':inpatients, 'rooms': rooms})

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
                print(room_id)
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
    for patients_id, patients_data in patients.items():
        for appointment_id, appointment_data in appointments.items():
            if appointment_data['doctorUID'] == uid and patients_id == appointment_data['patientName']:
                chosenPatients[patients_id] = patients_data

    chosenPatientData= {}
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
    medications_cursor = collection.find({}, {"Drug": 1, "_id": 0})
    medicines_list = [medication['Drug'] for medication in medications_cursor]
    
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

        while len(next_available_dates) < 4 and days_checked < 60:  # Check up to 30 days
            if current_day_of_week in available_days_numbers:
                # Check if there are no appointments on this date
                if current_date.date() not in [datetime.strptime(appointment_data['appointmentDate'], "%Y-%m-%d").date() for appointment_data in upcoming_appointments.values()]:
                    list_final.append(current_date.date())

            current_date += timedelta(days=1)
            current_day_of_week = (current_day_of_week + 1) % 7
            days_checked += 1

        print('List Final is ', list_final)
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
        print('three_days_after', three_days_after)

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
    
    if time_slots:
        earliest_time = min(time_slots)
        print("Earliest time slot:", earliest_time)
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
    for vitalsigns_id, vitalsigns_data in vitalsigns.items():
        if chosenPatient == vitalsigns_id:
            for vsid, vsdata in vitalsigns_data.items():
                chosenPatientVitalEntryData[vsid] = vsdata
    
    sorted_vital_signs = dict(sorted(chosenPatientVitalEntryData.items(), key=lambda item: date.datetime.strptime(item[1]['date'] + ' ' + item[1]['time'], "%Y-%m-%d %I:%M %p"), reverse=True))
    

    chosenPatientConsulNotes = {}

    consultation_notes_ref = db.child("consultationNotes").child(chosenPatient)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = consultation_notes_ref.child(date1).get().val()
    if consulnotes_data:
        chosenPatientConsulNotes[chosenPatient] = consulnotes_data
        if 'diagnosis' in consulnotes_data:
            currdiagnosis = consulnotes_data['diagnosis']
        else:
            currdiagnosis = None

    medications_cursor = collection.find({}, {"Disease": 1, "_id": 0})
    medicines_set = {medication['Disease'] for medication in medications_cursor}
    medicines_list = list(medicines_set)

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
            db.child('testrequest').child(chosenPatient).child(id).set(data)


        if 'endAppointment' in request.POST:
            appointment_id = request.POST.get('endAppointment')
            
            # Check if the follow-up checkbox is checked
            if 'followupCheckbox' in request.POST:
                followup_appointment()
                print('PASS')
            
            # Update the appointment status to 'Finished' in the database
            db.child("appointments").child(endAppointment).update({'status': 'Finished'})
            
            # Redirect to the DoctorDashboard
            return redirect('DoctorDashboard')


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
            print(todaydate, chosenPatient, medicine_name, dosage, route, frequency, additional_remarks)
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

            for freq in frequency:
                if freq == "Once Daily":
                    times_list.extend(request.POST.getlist('times-once-daily[]'))
                elif freq == "Twice Daily":
                    times_list.append(', '.join(request.POST.getlist('times-twice-daily[]')))
                elif freq == "Thrice Daily":
                    times_list.append("Morning, Afternoon, Evening")

            for freq in frequency:
                if freq == "Once Daily":
                    occurence = 1
                elif freq == "Twice Daily":
                    occurence = 2
                elif freq == "Thrice Daily":
                    occurence = 3

            data = {
                'patient_id': chosenPatient,
                'prescriptionsoderUID': qid,
                'todaydate': todaydate,
                'endDate': endDate_str,
                'times': times_list,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'route': route,
                'frequency': frequency,
                'additional_remarks': additional_remarks,
                'status': 'Ongoing'
            }

            
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
                        'disease': None,
                        'room': None,
                        'lastVisited': date1
                    })

            for index in range(len(medicine_name)):
                print(len(medicine_name))
                print(len(dosage))
                print(len(route))
                print(len(frequency))
                print(len(additional_remarks))
                print(len(times_list))

                qid = str(uuid.uuid1())
                medicine = medicine_name[index]
                dosage_value = dosage[index]
                route_value = route[index]
                frequency_value = frequency[index]
                additional_remarks_value = additional_remarks[index]
                times_value = times_list[index]

                # Now you can use these values to construct your data dictionary and save to the database
                data = {
                    'date': endDate_str,
                    'prescriptionsoderUID': qid,
                    'occurence': occurence,
                    'medicine_name': medicine,
                    'dosage': dosage_value,
                    'route': route_value,
                    'frequency': frequency_value,
                    'additional_remarks': additional_remarks_value,
                    'patient_id': chosenPatient,
                    'todaydate': todaydate,
                    'status': 'Ongoing',
                    'times': times_value
                }

                db.child('patientsorders').child(chosenPatient).child(todaydate).child(qid).set(data)
                
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
            print('SELECTED TIME', selected_time)
            followup_time = request.POST.get('followup_time')

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
                'appointmentTime': followup_time,
                'appointmentVisitType': 'Follow-Up Visit',
                'doctorUID': uid1,
                'patientName': chosenPatient,
                'status': 'Ongoing'
            }
            db.child('appointments').child(new_id).set(data2)
 
        if 'admitButton' in request.POST:

            currdiagnosis = request.POST.get("currdiagnosis")
            # print(currdiagnosis)
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
                    print(chosen_room_id)
                    room_data = rooms[chosen_room_id]
                    room_patients = room_data.get('patients', [])
                    room_patients.append(chosenPatient)
                    db.child("rooms").child(chosen_room_id).update({'patients': room_patients})


                    db.child("patientdata").child(chosenPatient).update({
                        'status': 'Inpatient',
                        'disease': currdiagnosis,
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
    medications_cursor = collection.find({}, {"Drug": 1, "_id": 0})
    medicines_list = [medication['Drug'] for medication in medications_cursor]

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
        else:
            currdiagnosis = None                  

    medications_cursor = collection.find({}, {"Disease": 1, "_id": 0})
    medicines_set = {medication['Disease'] for medication in medications_cursor}
    medicines_list = list(medicines_set)

    progressnotes = db.child("progressnotes").get().val()
    nurses = db.child("nurses").get().val()

    print('SORTED APPOINTMENTS ARE ', sorted_appointments)
    
    first_appointment = next(iter(sorted_appointments.values()), None)
    print('FIRST APPOINTMENTS IS ', first_appointment)
    first_appointment_date = first_appointment['appointmentDate'] if first_appointment else None
    print('CONVERTED FIRST DATE IS ', first_appointment_date)
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
                                                                                'medicines_list': medicines_list,
                                                                                'next_available_dates': next_available_dates,
                                                                                'num_days': num_days,
                                                                                'nurses': nurses,
                                                                                'nearest_dates': nearest_dates,
                                                                                'earliest_time': earliest_time,
                                                                                'three_days_after': three_days_after})

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

    if diagnosis == 'Others':
        diagnosis = request.POST.get('otherDiagnosis')
    
    # Save Chief Compliant into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

    # Update appointment data in Firebase
    if diagnosis:
        db.child(appointment_path).update({
            'patientID': id,
            'doctorID': uid,
            'diagnosis': diagnosis
        })


#Calculate age function for retrieving patient data

def calculate_age(birthday):
    today = datetime.today()
    print(today)
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

def add_vitalsign_entry(request):
    return render(request, 'hmis/add_vitalsign_entry.html')

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
    patientmedicalhistory = db.child("patientmedicalhistory").child(chosen_patient_uid).child('pastHistory').get().val()
    patientAllergyHistory = db.child("patientmedicalhistory").child(chosen_patient_uid).child('allergyhistory').get().val()
    patientImmunizationHistory = db.child("patientmedicalhistory").child(chosen_patient_uid).child('immunizationHistory').get().val()
    patientFamilyhistory = db.child("patientmedicalhistory").child(chosen_patient_uid).child('familyHistory').get().val()
    patientSocialhistory = db.child("patientmedicalhistory").child(chosen_patient_uid).child('socialHistory').get().val()
    uid = request.session['uid'] 
    chosenPatient = request.GET.get('chosenPatient', '')
    consulNotes = db.child("consultationNotes").get().val()

    patientMedical = db.child("patientmedicalhistory").get().val()
    if request.method == 'POST':
        if 'saveMedicalHistoryButton' in request.POST:
            diagnosis = request.POST.getlist('diagnosis_surgical')
            date_illness = request.POST.getlist('date_illness')
            treatment = request.POST.getlist('treatment')
            remarks = request.POST.getlist('remarks')
            
            data = {
                'patient_id': chosen_patient_uid,
                'diagnosis_surgical': diagnosis,
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
            alcohol = request.POST.get('alcohol')
            
            data = {
                'patient_id': chosen_patient_uid,
                'smoking': smoking,
                'alcohol': alcohol
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('socialHistory').update(data)

    return render(request, 'hmis/patient_medical_history.html', {'patientmedicalhistory': patientmedicalhistory,
                                                                 'patientAllergyHistory': patientAllergyHistory,
                                                                 'patientImmunizationHistory': patientImmunizationHistory,
                                                                 'patientFamilyhistory': patientFamilyhistory,
                                                                 'patientSocialhistory': patientSocialhistory,
                                                                 'doctors': doctors,
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
    print(sorted_dates)
    
    # Get the latest date
    latest_date = sorted_dates[0] if sorted_dates else None
    print(latest_date)

    chosenPatientTreatmentPlan = {}
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = prescriptionsorders_ref.child(latest_date).get().val()
    if consulnotes_data:
        chosenPatientTreatmentPlan[chosen_patient_uid] = consulnotes_data
    
    print(chosenPatientTreatmentPlan)
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


def patient_medication_nurse(request):
    return render(request, 'hmis/patient_medication_nurse.html')

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

def inpatient_medication_order(request):
    return render(request, 'hmis/inpatient_medication_order.html')

def perform_ocr(request):
    id = str(uuid.uuid1())
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        img = Image.open(uploaded_image)

        # encoded_image = base64.b64encode(img.tobytes()).decode('utf-8')
        # ref = f"/images/"
        # db.child(ref).update({
        #     'image_data': encoded_image
        # }) 
        # ref.push({'image_data': encoded_image})

        text = pytesseract.image_to_string(img)
        return HttpResponse(text)
    
    # Return a bad request response if no image is uploaded or if request method is not POST
    return HttpResponse('No image uploaded or invalid request.')

def pharmacy_drugs(request):
    #collection = connect_to_mongodb()
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
    patient_uid = request.GET.get('chosenPatient')
    diagnosis = request.GET.get('diagnosis')
    medications_cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2,})
    medicines_set = {medication['Drug'] for medication in medications_cursor if medication['Disease'] == diagnosis}
    medicines_list = list(medicines_set)
    cursor = collection.find({}, {"Disease": 1, "_id": 0, "Drug": 2, "Strength": 3, "Route": 4})
    pharmacy_lists = [{'Drug': medication['Drug'], 'Strength': medication['Strength'], 'Route': medication['Route']} for medication in cursor]
    pharmacy_lists_json = json.dumps(pharmacy_lists)
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 


    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 
                                                                     'medicines_list': medicines_list, 
                                                                     'pharmacy_lists':pharmacy_lists_json,
                                                                     'patient_uid': patient_uid,
                                                                     'doctors': doctors,
                                                                     'uid': uid})



def save_prescriptions(request):
    if request.method == 'POST':
        patient_uid = request.GET.get('chosenPatient')
        patientdata = db.child("patientdata").child(patient_uid).get().val()
        print(patientdata)
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
        # occurence = 0
        # for time in times:
        #     if time == 'Morning':
        #         occurence += 1
        #     if time == 'Afternoon':
        #         occurence += 1
        #     if time == 'Evening':
        #         occurence += 1

        try:
            id = str(uuid.uuid1())
            status = 'Ongoing'  # Default status

            # Check if endDate is reached
            if datetime.now() > endDate:
                status = 'Finished'

            data = {
                'prescriptionsoderUID': id,
                'days': days,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'route': route,
                #'frequency': occurence,
                'times': times,
                'additional_remarks': additional_remarks,
                'patient_id': patient_id,
                'todaydate': todaydate,
                'endDate': endDate_str,
                'status': status
            }
            db.child('prescriptionsorders').child(patient_id).child(todaydate).set(data)

            if patientdata['status'] == 'Inpatient':
                for index in range(len(medicine_name)):
                    pid = str(uuid.uuid1())
                    medicine = medicine_name[index]
                    dosage_value = dosage[index]
                    route_value = route[index]
                    additional_remarks_value = additional_remarks[index]
                    times_value = times_list[index]
                    days = days[index]

                    data = {
                        'date': endDate_str,
                        'prescriptionsoderUID': id,
                        'medicine_name': medicine,
                        'dosage': dosage_value,
                        'route': route_value,
                        'additional_remarks': additional_remarks_value,
                        'patient_id': patient_id,
                        'todaydate': todaydate,
                        'status': 'Ongoing',
                        'days': days,
                        'times': times_value
                    }

                    db.child('doctorsorders').child(patient_id).child(todaydate).child(pid).set(data)

            elif patientdata['status'] == 'Outpatient':
                # Create prescription PDF here
                prescription = generate_prescription_pdf(patient_uid, medicine_name, dosage, route, frequency, additional_remarks, times_list)
                return HttpResponse(prescription, content_type='application/pdf')

            messages.success(request, 'Prescription saved successfully!')
            return redirect(reverse('view_treatment_plan_all') + f'?chosenPatient={patient_uid}')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'hmis/view_treatment_plan.html', {'patient_uid': patient_uid})


def generate_prescription_pdf(patient_uid, medicine_name, dosage, route, frequency, additional_remarks, times_list):
    context = {
        'patient_uid': patient_uid,
        'medicine_name': medicine_name,
        'dosage': dosage,
        'route': route,
        'frequency': frequency,
        'additional_remarks': additional_remarks,
        'times_list': times_list
    }
    pdf = render_to_pdf('prescription_template.html', context)
    if pdf:
        return pdf
    else:
        # Handle PDF generation error
        messages.error(request, 'Error generating prescription PDF.')
        return None

def render_to_pdf(template_path, context):
    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return result.getvalue()
   


def diagnostic_lab_reports(request):
    return render(request, 'hmis/diagnostic_lab_reports.html')

def diagnostic_imagery_reports(request):
    submittedTest = db.child("submittedTest").get().val()
    
    chosenPatient = request.GET.get('chosenPatient', '')
    return render(request, 'hmis/diagnostic_imagery_reports.html', {'submittedTest': submittedTest, 'chosenPatient': chosenPatient})

def edit_medical_surgical_history(request):
    return render(request, 'hmis/edit_medical_surgical_history.html')

def edit_drug_history(request):
    return render(request, 'hmis/edit_drug_history.html')

def edit_allergy(request):
    return render(request, 'hmis/edit_allergy.html')

def edit_immunization_history(request):
    return render(request, 'hmis/edit_immunization_history.html')

def edit_family_history(request):
    if request.method == 'POST':
        if 'saveFamilyHistory' in request.POST:
            id = str(uuid.uuid1())
            member = request.POST.get('member-input-1')
            illness = request.POST.get('illness-input-1')
            age = request.POST.get('age-data-input-1')

            # Format the data as needed
            data = {
                'member': member,
                'illness': illness,
                'age': age
            }
            
            db.child('patientmedicalhistory').child(id).child('familyhistory').set(data)

    return render(request, 'hmis/edit_family_history.html')

def view_image(request, submitted_id):
    ref = db.reference('/images')  # Assuming images are stored under '/images' node in Firebase
    snapshot = ref.order_by_key().equal_to(submitted_id).get()
    
    if snapshot:
        image_data = snapshot[submitted_id]['image_data']
        # Decode base64 image data
        decoded_image = base64.b64decode(image_data)
        
        # Render the image in the template
        return render(request, 'view_image.html', {'image_data': decoded_image})
    else:
        return HttpResponse('Image not found')