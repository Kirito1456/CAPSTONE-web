# your_app/management/commands/firebase_listener.py
import time
import pyrebase
from django.core.management.base import BaseCommand
from hmis.models import Notification, Staff
import signal
import threading

# Firebase configuration
config={
    "apiKey": "AIzaSyC0JRWGF4OsRL7-OrsP6F7G15Np5MJzjs4",
   "authDomain": "hmis-a3bbe.firebaseapp.com",
    "databaseURL": "https://hmis-a3bbe-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "hmis-a3bbe",
    "storageBucket": "hmis-a3bbe.appspot.com",
    "messagingSenderId": "796086831145",
    "appId": "1:796086831145:web:8c4e1406b3bf17f875f438",
    "measurementId": "G-GWES7Z6T2N"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

class Command(BaseCommand):
    help = 'Start Firebase listener for test result uploads'

    def handle(self, *args, **kwargs):

        Notification.objects.all().delete()
        print("Cleared all existing notifications.")
        
        stop_event = threading.Event()

        def stream_handler(message):
            try:
                print(f"Received message: {message}")
                patients = db.child("patients").get().val()
                if message["event"] == "put" and message["data"] is not None:
                    print("Processing")
                    for patient_id, tests in message["data"].items():
                        print("Processing2")
                        print(tests)
                        if isinstance(tests, dict):
                            print("Processing3")
                            for test_id, test_data in tests.items():
                                print("Processing4")
                                patient_id = test_data.get('patient')
                                for id, patient_data in patients.items():
                                    if patient_id == id:
                                        name = patient_data.get('fname') + ' ' + patient_data.get('lname')
                                uid = test_data.get('doctor')
                                date = test_data.get('date')
                                download_url = test_data.get('downloadURL')
                                
                                test_request_key = test_data.get('testRequestKey')
                                if uid:
                                    print("Processing5")
                                    print(f"Creating notification for {test_request_key}")
                                    Notification.objects.create(firebase_id=uid, 
                                                                message=f'Patient {name} uploaded new test result for {test_request_key}', 
                                                                created_at=date,
                                                                patient_id=patient_id,
                                                                is_read=False,
                                                                type = 'diagnostic',)
                        else:
                            uid = message["data"].get('doctor')
                            date = message["data"].get('date')
                            download_url = message["data"].get('downloadURL')
                            patient_id = test_data.get('patient')
                            for id, patient_data in patients.items():
                                    if patient_id == id:
                                        name = patient_data.get('fname') + ' ' + patient_data.get('lname')
                            test_request_key = message["data"].get('testRequestKey')
                            if uid:
                                print("Processing5")
                                print(f"Creating notification for {test_request_key}")
                                Notification.objects.create(firebase_id=uid, 
                                                            message=f'Patient {name} uploaded new test result for  {test_request_key}', 
                                                            created_at=date,
                                                            patient_id=patient_id,
                                                            is_read=False,
                                                            type = 'diagnostic',)
                            break
            except Exception as e:
                print(f"Error processing message: {e}")
        
        def appointments_stream_handler(message):
            try:
                print(f"Received appointments message: {message}")
                if message["event"] == "put" and message["data"] is not None:
                    if isinstance(message["data"], dict) and message["path"] == '/' :
                        for appointment_id, appointment_data in message["data"].items():
                            process_appointment_data(appointment_id, appointment_data)
                    else:
                        # Extract appointment_id from the path
                        appointment_id = message["path"].split('/')[1]
                        appointment_data = message["data"]
                        print(appointment_id)
                        print(appointment_data)
                        if isinstance(appointment_data, dict):
                            process_appointment_data(appointment_id, appointment_data)
                        else:
                            appointment_data1 = db.child("appointments").child(appointment_id).get().val()
                            print(appointment_data1)
                            process_appointment_data(appointment_id, appointment_data1)
            except Exception as e:
                print(f"Error processing appointments message: {e}")

        def process_appointment_data(appointment_id, appointment_data):
            try:
                patients = db.child("patients").get().val()
                print(f"Processing appointment data: {appointment_data}")
                if appointment_data.get('status') == 'Confirmed':
                    doctor_uid = appointment_data.get('doctorUID')
                    patient_name = appointment_data.get('patientName')
                    for id, patient_data in patients.items():
                        if patient_name == id:
                            name = patient_data.get('fname') + ' ' + patient_data.get('lname')
                    appointment_date = appointment_data.get('appointmentDate')
                    appointment_time = appointment_data.get('appointmentTime')
                    type_appointment = appointment_data.get('appointmentVisitType')
                    Notification.objects.create(
                        firebase_id=doctor_uid,
                        message=f'You have an appointment with {name} ({type_appointment}) on {appointment_date} at {appointment_time}',
                        created_at=appointment_date,
                        is_read=False,
                        type = 'appointment'
                    )
            except Exception as e:
                print(f"Error processing appointment data: {e}")

        def symptoms_stream_handler(message):
            try:
                print(f"Received symptoms message: {message}")
                if message["event"] == "put" and message["data"] is not None:
                    process_symptom_data(message["data"])
            except Exception as e:
                print(f"Error processing symptoms message: {e}")
        
        def process_symptom_data(symptom_data):
            try:
                patients = db.child("patients").get().val()
                for patient_id, symptoms in symptom_data.items():
                    for symptom_name, symptom_details in symptoms.items():
                        if "severityRecords" in symptom_details:
                            for date, time_records in symptom_details["severityRecords"].items():
                                for time, severity in time_records.items():
                                    if severity in [3, 4]:
                                        print(f"High severity detected: {severity} for {symptom_name} on {date} at {time}")
                                        for id, patient_data in patients.items():
                                            if patient_id == id:
                                                name = patient_data.get('fname') + ' ' + patient_data.get('lname')
                                        Notification.objects.create(
                                            message=f'Patient {name} has a high severity of {severity} for {symptom_name} on {date} at {time}.',
                                            created_at=date,
                                            patient_id=patient_id,
                                            is_read=False,
                                            type='symptom',
                                        )
            except Exception as e:
                print(f"Error processing symptom data: {e}")
                
         # Define a function to stop the listener
        def stop_listener(signal, frame):
            print("Stopping Firebase listener...")
            stop_event.set()

        # Register the stop signal
        signal.signal(signal.SIGINT, stop_listener)
        signal.signal(signal.SIGTERM, stop_listener)

        # Set up a listener on the Firebase Realtime Database
        my_stream = db.child("submittedTest").stream(stream_handler)
        appointments_stream = db.child("appointments").stream(appointments_stream_handler)
        symptoms_stream = db.child("symptoms").stream(symptoms_stream_handler)

        # Keep the script running until stop_event is set
        try:
            while not stop_event.is_set():
                print("Firebase listener.....")
                time.sleep(2)
        finally:
            my_stream.close()
            appointments_stream.close()
            symptoms_stream.close()
            print("Firebase listener stopped.")