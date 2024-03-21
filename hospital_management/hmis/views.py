from datetime import datetime , timedelta
import datetime as date
from django.shortcuts import render, redirect
from django.contrib import messages
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database
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

# Use the firebase_database object directly
db = firebase_database

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
    #print(request.session['uid'])
    
    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    upcomings = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']    

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

    # Pass the combined data to the template
    return render(request, 'hmis/AppointmentUpcoming.html', {'appointments': sorted_upcoming_appointments, 
                                                             'patients': patients, 'uid': uid, 'doctors': doctors})


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
            new_date = request.POST.get('new-appointment-date')
            new_time = request.POST.get('new-appointment-time')
            print(appID)

            # Format time and date objects to desired format
            new_time_formatted = date.datetime.strptime(new_time, "%H:%M")
            #new_date_formatted = new_time_formatted.strftime("%I:%M %p")            
            print(new_time_formatted)

            new_time_str = new_time_formatted.strftime("%I:%M %p")
            print(new_time_str)

            # Construct the path to the appointment data in Firebase
            appointment_path = f"/appointments/{appID}"  # Adjust the path as per your Firebase structure

            # Update appointment data in Firebase
            db.child(appointment_path).update({
                'appointmentDate': new_date,
                'appointmentTime': new_time_str,
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
    endAppointment = request.GET.get('appointment_id', '')
    appointmentschedule = db.child("appointmentschedule").get().val()
    print(endAppointment)
    time_slots = []
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()

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


    print(time_slots)

    if request.method == 'POST':
        try:
            id=str(uuid.uuid1())
            appID = request.POST.get('appID')
            new_date = request.POST.get('new-appointment-date')
            new_time = request.POST.get('new-appointment-time')
            doctor = request.session['uid']
            print(appID)
            print(id)
            print(doctor)
            print(new_date)

            # Convert to datetime object
            time_obj = datetime.strptime(new_time, "%H:%M")

            # Convert to 12-hour format with AM/PM
            time_12h = time_obj.strftime("%I:%M %p")

            # Format time and date objects to desired format
            #new_time_formatted = date.datetime.strptime(new_time, "%H:%M")
            #new_date_formatted = new_time_formatted.strftime("%I:%M %p")            
            #print(new_time_formatted)

            #new_time_str = new_time_formatted.strftime("%I:%M %p")
            #print(new_time_str)

            # Construct the path to the appointment data in Firebase
            appointment_path = f"/appointments/{id}"  # Adjust the path as per your Firebase structure

            # Update appointment data in Firebase
            db.child(appointment_path).set({
                'doctorUID': doctor,
                'appointmentVisitType': "Follow-Up Visit",
                'appointmentDate': new_date,
                'appointmentTime': time_12h,
                'status': 'Ongoing',
                'patientName': appID
            }) 
            appointment_path1 = f"/appointments/{endAppointment}"
            db.child(appointment_path1).update({
                'status': 'Finished'
            }) 

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('DoctorDashboard')  # Redirect to the appointments list page

    return render(request, 'hmis/AppointmentUpcoming.html', {'uid': uid,
                                                            'appointmentschedule': appointmentschedule,
                                                            'time_slots': time_slots})
        

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
                        if patientdata_data["status"] == 'Inpatient' and patientdata_data['patientid'] == appointment_data["patientName"]:
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
    # today = datetime.now()
    # tomorrow = today + timedelta(days=1)
    # date = tomorrow.strftime('%Y-%m-%d')
    date = datetime.today().strftime('%Y-%m-%d')
    doctors = db.child("doctors").get().val()
    uid = request.session['uid'] 
    medications_cursor = collection.find({}, {"Generic Name": 1, "_id": 0})
    medicines_list = [medication['Generic Name'] for medication in medications_cursor]

    chosenPatient = request.GET.get('chosenPatient', '')
    endAppointment = request.GET.get('appointment_id', '')

    appointmentschedule = db.child("appointmentschedule").get().val()
    doctorSched = db.child("appointmentschedule").child(uid).get().val()

    time_slots = []
    appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
    
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


    print(booked_times)
    print(time_slots)
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
        if "patientid" in patientsdata_data:
            if chosenPatient == patientsdata_data["patientid"]:
                chosenPatientDatas[patientsdata_id] = patientsdata_data

    #Get Vital Signs Data of Chosen Patient
    chosenPatientVitalEntryData = {}
    for vitalsigns_id, vitalsigns_data in vitalsigns.items():
        if chosenPatient == vitalsigns_data["patientid"]:
            chosenPatientVitalEntryData[vitalsigns_id] = vitalsigns_data

    chosenPatientConsulNotes = {}
    # for consulnotes_id, consulnotes_data in consulnotes.items():
    #     if chosenPatient == consulnotes_data.data["patientID"] and date == consulnotes_data["date"]:
    #         chosenPatientConsulNotes[consulnotes_id] = consulnotes_data

    consultation_notes_ref = db.child("consultationNotes").child(chosenPatient)
    # Retrieve the data for the specified patient ID and date
    consulnotes_data = consultation_notes_ref.child(date).get().val()
    if consulnotes_data:
        chosenPatientConsulNotes[chosenPatient] = consulnotes_data
        currdiagnosis = consulnotes_data['diagnosis']

    if request.method == 'POST':

        if 'complaintButton' in request.POST:
            save_chiefComplaint(request)

        if 'rosButton' in request.POST:
            save_review_of_systems(request)

        if 'diagnosisButton' in request.POST:
            save_diagnosis(request)
        
        if 'submitLabTestRequest' in request.POST:
            id = str(uuid.uuid1())
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
                'pet_scan': pet_scan
            }
            
            # Save the data to the database
            db.child('testrequest').child(chosenPatient).child(id).set(data)


        if 'endAppointment' in request.POST:
            db.child("appointments").child(endAppointment).update({'status': 'Finished'})
            return redirect('DoctorDashboard')

        if 'addDischargePrescription' in request.POST:
            medicine_name = request.POST.getlist('medicineName1')
            dosage = request.POST.getlist('dosage1')
            route = request.POST.getlist('route1')
            frequency = request.POST.getlist('frequency1')
            additional_remarks = request.POST.getlist('remarks1')  
            todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(todaydate, chosenPatient, medicine_name, dosage, route, frequency, additional_remarks)

            data = {
                'patient_id': chosenPatient,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'route': route,
                'frequency': frequency,
                'additional_remarks': additional_remarks,
                'todaydate': todaydate
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
                    'appointmentDate': appointment_date,
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
                        'lastVisited': date
                    })
 
        if 'admitButton' in request.POST:

            #currdiagnosis = request.POST.get("currdiagnosis")
            print(currdiagnosis)
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
        date = datetime.today().strftime('%Y-%m-%d')
        doctors = db.child("doctors").get().val()
        uid = request.session['uid'] 
        medications_cursor = collection.find({}, {"Generic Name": 1, "_id": 0})
        medicines_list = [medication['Generic Name'] for medication in medications_cursor]

        chosenPatient = request.GET.get('chosenPatient', '')

        appointmentschedule = db.child("appointmentschedule").get().val()
        doctorSched = db.child("appointmentschedule").child(uid).get().val()

        time_slots = []
        appointmentschedule_data = db.child("appointmentschedule").child(uid).get().val()
        

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


        print(time_slots)
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
            if "patientid" in patientsdata_data:
                if chosenPatient == patientsdata_data["patientid"]:
                    chosenPatientDatas[patientsdata_id] = patientsdata_data

        #Get Vital Signs Data of Chosen Patient
        chosenPatientVitalEntryData = {}
        for vitalsigns_id, vitalsigns_data in vitalsigns.items():
            if chosenPatient == vitalsigns_data["patientid"]:
                chosenPatientVitalEntryData[vitalsigns_id] = vitalsigns_data

        chosenPatientConsulNotes = {}
        # for consulnotes_id, consulnotes_data in consulnotes.items():
        #     if chosenPatient == consulnotes_data.data["patientID"] and date == consulnotes_data["date"]:
        #         chosenPatientConsulNotes[consulnotes_id] = consulnotes_data

        consultation_notes_ref = db.child("consultationNotes").child(chosenPatient)
        # Retrieve the data for the specified patient ID and date
        consulnotes_data = consultation_notes_ref.child(date).get().val()
        if consulnotes_data:
            chosenPatientConsulNotes[chosenPatient] = consulnotes_data
            currdiagnosis = consulnotes_data['diagnosis']                                                         #'room': 201,})


    return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 
                                                                                'chosenPatientDatas': chosenPatientDatas, 
                                                                                'chosenPatientVitalEntryData': chosenPatientVitalEntryData,
                                                                                'chosenPatientConsulNotes': chosenPatientConsulNotes,
                                                                                'doctors': doctors,
                                                                                'uid': uid,
                                                                                'medicines_list': medicines_list,
                                                                                'appointmentschedule': appointmentschedule,
                                                                                'time_slots': time_slots})
    # return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 'chosenPatientDatas': chosenPatientDatas, 'chosenPatientVitalEntryData': chosenPatientVitalEntryData, 'chosenPatientAge' : chosenPatientAge})

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
        if chosenPatient == vitalsigns_data["patientid"]:
            chosenPatientVitalEntryData[vitalsigns_id] = vitalsigns_data
    return render(request, 'hmis/patient_vital_signs_history.html', {'chosenPatientData': chosenPatientData, 
                                                                     'chosenPatientVitalEntryData': chosenPatientVitalEntryData, 
                                                                     'doctors': doctors,
                                                                     'uid': uid})

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
            diagnosis = request.POST.getlist('diagnosis')
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
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        img = Image.open(uploaded_image)
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
    medications_cursor = collection.find({}, {"Generic Name": 1, "_id": 0})
    medicines_list = [medication['Generic Name'] for medication in medications_cursor]
    doctors = db.child('doctors').get().val()
    uid = request.session['uid'] 

    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 
                                                                     'medicines_list': medicines_list, 
                                                                     'patient_uid': patient_uid,
                                                                     'doctors': doctors,
                                                                     'uid': uid})

def save_prescriptions(request):
    patient_uid = request.GET.get('chosenPatient')
    print(patient_uid)
    if request.method == 'POST':
        numOfDays = int(request.POST.get('numOfDays'))  # Convert to integer
        todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate endDate
        todaydate_datetime = datetime.strptime(todaydate, "%Y-%m-%d %H:%M:%S")
        endDate = todaydate_datetime + timedelta(days=numOfDays)

        endDate_str = endDate.strftime("%Y-%m-%d %H:%M:%S")

        patient_id = patient_uid 
        medicine_name = request.POST.getlist('medicine_name')
        dosage = request.POST.getlist('dosage')
        route = request.POST.getlist('route')
        frequency = request.POST.getlist('frequency')
        additional_remarks = request.POST.getlist('additionalremarks')  
        todaydate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(todaydate, patient_id, medicine_name, dosage, route, frequency, additional_remarks)
        try:
            id = str(uuid.uuid1())
            status = 'Ongoing'  # Default status

            # Check if endDate is reached
            if datetime.now() > endDate:
                status = 'Finished'

            data = {
                'prescriptionsoderUID': id,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'route': route,
                'frequency': frequency,
                'additional_remarks': additional_remarks,
                'patient_id': patient_id,
                'todaydate': todaydate,
                'endDate': endDate_str,
                'status': status
            }
            db.child('prescriptionsorders').child(patient_id).child(todaydate).set(data)

            messages.success(request, 'Prescription saved successfully!')
            return redirect(request.META.get('HTTP_REFERER', ''))
        #add alerts
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'hmis/view_treatment_plan.html', {'patient_uid': patient_uid})



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