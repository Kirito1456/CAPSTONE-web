import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database
from hmis.forms import StaffRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import logout as auth_logout
from django.core.mail import send_mail
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
            for account in accounts.values():
                if account["role"] == "Doctor" and account["email"] == email:
                    doctor_found = True
                    break

            if doctor_found:
                return redirect('AppointmentUpcoming')
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
                # Create user in Firebase Authentication
                user = firebase_auth.create_user_with_email_and_password(email, password)
                #print(user)

                # Adjust this line according to the actual structure of the response object
                #uid = user['localId']  # Accessing 'localId' from the user object
    
                 # Ensure you have the correct value of uid
                #print(user['localId'])

                # Get idToken from the session (if needed)
                #idToken = request.session['uid']
                
                data = {
                    'uid': user['localId'],
                    'fname': cleaned_data['fname'],
                    'lname': cleaned_data['lname'],
                    #'cnumber': '',
                    'sex': cleaned_data['sex'],
                    'role': cleaned_data['role'],
                    'specialization': cleaned_data['specialization'],
                    'department': cleaned_data['department'],
                    'clinic': cleaned_data['clinic'],
                    #'clinicaddress': cleaned_data['clinicaddress'],
                    'email': email,
                }

                # Save the form data to the database
                # db.child('staff').child(user['localId']).set(data)

                if (cleaned_data['role'] == 'Doctor'):
                    db.child('doctors').child(user['localId']).set(data)
                else:
                    db.child('nurses').child(user['localId']).set(data)
                
                
                
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
                appointment_datetime = datetime.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
            
                # Check if appointment date is in the future
                if appointment_datetime >= datetime.datetime.now():
                    upcoming_appointments[appointment_id] = appointment_data

    # Sort appointments by date
    sorted_upcoming_appointments = dict(sorted(upcoming_appointments.items(), key=lambda item: datetime.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))

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
            print(new_time)

            # Format time and date objects to desired format
            new_time_formatted = datetime.datetime.strptime(new_time, "%H:%M")
            #new_date_formatted = new_time_formatted.strftime("%I:%M %p")            
            print(new_time_formatted)

            new_time_str = new_time_formatted.strftime("%I:%M %p")
            print(new_time_str)

            # Construct the path to the appointment data in Firebase
            appointment_path = f"/appointments/{appID}"  # Adjust the path as per your Firebase structure

            # Update appointment data in Firebase
            db.child(appointment_path).update({
                'appointmentDate': new_date,
                'appointmentTime': new_time_str
            }) 

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        return redirect('AppointmentUpcoming')  # Redirect to the appointments list page

    # Handle GET request or invalid form submission
    return redirect('AppointmentUpcoming')

def AppointmentPast(request):

    if request.session.get('uid') is None:
        return redirect('home')
    
    # Get data from Firebase
    pasts = db.child("appointments").get().val()
    patients = db.child("patients").get().val()
    doctors = db.child("doctors").get().val()
    uid = request.session['uid']

    # Filter and sort upcoming appointments
    past_appointments = {}
    for appointment_id, appointment_data in pasts.items():
        if appointment_data["doctorUID"] == uid:
            appointment_date_str = appointment_data.get("appointmentDate", "")
            appointment_time_str = appointment_data.get("appointmentTime", "")
        
            if appointment_date_str and appointment_time_str:
            # Convert appointment date string to datetime object
                appointment_datetime = datetime.datetime.strptime(appointment_date_str + " " + appointment_time_str, "%Y-%m-%d %I:%M %p")
            
            # Check if appointment date is in the future
                if appointment_datetime < datetime.datetime.now():
                    past_appointments[appointment_id] = appointment_data

    # Sort appointments by date
    sorted_past_appointments = dict(sorted(past_appointments.items(), key=lambda item: datetime.datetime.strptime(item[1]['appointmentDate'] + ' ' + item[1]['appointmentTime'], "%Y-%m-%d %I:%M %p")))

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