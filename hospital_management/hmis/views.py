from django.shortcuts import render, redirect
from django.contrib import messages
from hmis.models import Medications
from hospital_management.settings import auth as firebase_auth
from hospital_management.settings import database as firebase_database
from hospital_management.settings import collection 
from hmis.forms import StaffRegistrationForm, MedicationsListForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage

from datetime import datetime
from PIL import Image 
from pytesseract import pytesseract 

import uuid
import json


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
    doctors = db.child("doctors").get().val()
    

    # Pass the patients data to the template
    return render(request, 'hmis/patient_data_doctor_view.html', {'patients': patients, 'patientsdata': patientsdata, 'doctors': doctors})

def patient_personal_information_inpatient(request):
    patients = db.child("patients").get().val()
    patientsdata = db.child("patientdata").get().val()
    vitalsigns = db.child("vitalsigns").get().val()
    consulnotes = db.child("consultationNotes").get().val()
    date = datetime.today().strftime('%Y-%m-%d')

    chosenPatient = request.GET.get('chosenPatient', '')

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

    if request.method == 'POST':

        if 'complaintButton' in request.POST:
            save_chiefComplaint(request)

        if 'rosButton' in request.POST:
            save_review_of_systems(request)

        if 'diagnosisButton' in request.POST:
            save_diagnosis(request)
        
        if 'submitLabTestRequest' in request.POST:
            print(chosenPatient)
            id = str(uuid.uuid1())
            request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            blood_test = request.POST.get('bloodTestCheckbox', False)
            chest_xray = request.POST.get('chestXrayCheckbox', False)
            urine_test = request.POST.get('urineTestCheckbox', False)
            
            data = {
                'patient_id': chosenPatient,
                'datetime': request_time,
                'blood_test': blood_test,
                'chest_xray': chest_xray,
                'urine_test': urine_test
            }
            db.child('testrequest').child(id).set(data)

    return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 
                                                                                'chosenPatientDatas': chosenPatientDatas, 
                                                                                'chosenPatientVitalEntryData': chosenPatientVitalEntryData,
                                                                                'chosenPatientConsulNotes': chosenPatientConsulNotes})
    # return render(request, 'hmis/patient_personal_information_inpatient.html', {'chosenPatientData': chosenPatientData, 'chosenPatientDatas': chosenPatientDatas, 'chosenPatientVitalEntryData': chosenPatientVitalEntryData, 'chosenPatientAge' : chosenPatientAge})

def save_chiefComplaint(request):
        
    #if request.method == 'POST':
        #uid = str(uuid.uuid1())
        date = datetime.today().strftime('%Y-%m-%d')
        chiefComplaint = request.POST.get('chiefComplaint')
        id = request.POST.get('complaintButton') 
        
        # Save Chief Compliant into Firebase Database
        appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

        # Update appointment data in Firebase
        if chiefComplaint:
            db.child(appointment_path).update({
                'patientID': id,
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

    # Save into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

    # if not isinstance(skin_conditions, list):
    #     skin_conditions = [skin_conditions]
    #  Update appointment data in Firebase
    

    db.child(appointment_path).update({
        'patientID': id,
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

    if diagnosis == 'Others':
        diagnosis = request.POST.get('otherDiagnosis')
    
    # Save Chief Compliant into Firebase Database
    appointment_path = f"/consultationNotes/{id}/{date}"  # Adjust the path as per your Firebase structure

    # Update appointment data in Firebase
    if diagnosis:
        db.child(appointment_path).update({
            'patientID': id,
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
    return render(request, 'hmis/patient_vital_signs_history.html', {'chosenPatientData': chosenPatientData, 'chosenPatientVitalEntryData': chosenPatientVitalEntryData})

def patient_medical_history(request):
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    if request.method == 'POST':
        if 'saveAllergyButton' in request.POST:
            allergen = request.POST.getlist('allergen')
            severity = request.POST.getlist('severity')
            
            data = {
                'patient_id': chosen_patient_uid,
                'allergen': allergen,
                'severity': severity
            }
            db.child('patientmedicalhistory').child(chosen_patient_uid).child('allergyhistory').set(data)

    return render(request, 'hmis/patient_medical_history.html')

from datetime import datetime

def view_treatment_plan_all(request):
    chosen_patient_uid = request.GET.get('chosenPatient', None)
    patients = db.child("patients").get().val()

    # Retrieve prescription orders for the chosen patient from Firebase
    prescriptionsorders_ref = db.child("prescriptionsorders").child(chosen_patient_uid).get().val()
    
    prescriptionsorders_data = prescriptionsorders_ref.child('date')
    next_node_data = prescriptionsorders_data.get().val()
    print(next_node_data)
    dates = []
    if next_node_data:
        for doc_key, doc_data in next_node_data.items():
            datetime_str = doc_data.get('date')
            if datetime_str:
                # Parse datetime string to datetime object
                date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                dates.append(date)
    
    sorted_dates = sorted(dates, reverse=True)
    
    # Get the latest date
    latest_date = sorted_dates[0] if sorted_dates else None
    
    return render(request, 'hmis/view_treatment_plan.html', {
        'chosen_patient_uid': chosen_patient_uid,
        'patients': patients,
        'prescriptionsorders': prescriptionsorders_ref,
        'latest_date': latest_date
    })

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
    prescriptionsorders = db.child("prescriptionorders").get().val()
    return render(request, 'hmis/patient_medication_table.html', {'prescriptionsorders': prescriptionsorders})

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
    print(patient_uid)

    return render(request, 'hmis/outpatient_medication_order.html', {'patients': patients, 'medicines_list': medicines_list, 'patient_uid': patient_uid})

def save_prescriptions(request):
    patient_uid = request.GET.get('chosenPatient')
    print(patient_uid)
    if request.method == 'POST':
        
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
            data = {
                'prescriptionsoderUID': id,
                'medicine_name': medicine_name,
                'dosage': dosage,
                'route': route,
                'frequency': frequency,
                'additional_remarks': additional_remarks,
                'patient_id': patient_id,
                'todaydate': todaydate
            }
            db.child('prescriptionsorders').child(patient_id).child(todaydate).set(data)

            messages.success(request, 'Prescription saved successfully!')
            return redirect('view_treatment_plan_all')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'hmis/view_treatment_plan.html', {'patient_uid': patient_uid})

def diagnostic_lab_reports(request):
    return render(request, 'hmis/diagnostic_lab_reports.html')

def diagnostic_imagery_reports(request):
    return render(request, 'hmis/diagnostic_imagery_reports.html')

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

