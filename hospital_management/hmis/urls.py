from django.urls import path
from hmis import views
from .views import upload_image

urlpatterns = [
    # 
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('reset/', views.reset , name='reset'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
    path('logout/', views.logout, name='logout'),
    path('Profile.html', views.profile, name='Profile'),
    path('update_profile/', views.update_profile, name='update_profile'),

    # Appointments
    path('AppointmentUpcoming.html', views.AppointmentUpcoming, name='AppointmentUpcoming'),
    path('AppointmentScheduling.html', views.AppointmentScheduling, name='AppointmentScheduling'),
    path('AppointmentPast.html', views.AppointmentPast, name='AppointmentPast'),
    path('AppointmentCalendar.html', views.AppointmentCalendar, name='AppointmentCalendar'),

    # Nurses
    path('nursdashboard.html', views.NurseDashboard, name='NurseDashboard'),
    path('ChargeNurseDashboard.html', views.ChargeNurseDashboard, name='ChargeNurseDashboard'),
    #path('roomAssignments/', views.roomAssignments, name='roomAssignments'),
    
    path('doctordashboard.html', views.DoctorDashboard, name='DoctorDashboard'),

    path('delete_appointment/', views.delete_appointment, name='delete_appointment'),
    path('update_appointment/', views.update_appointment, name='update_appointment'),
    path('followup_appointment/', views.followup_appointment, name='followup_appointment'),
    path('clinics/', views.clinics, name='clinics'),
    path('nursesAdmin/', views.nursesAdmin, name='nursesAdmin'),

    # Patient Data Module
    path('patient_data_doctor_view/', views.patient_data_doctor_view, name='patient_data_doctor_view'),
    path('patient_vital_signs_history/', views.patient_vital_signs_history, name='patient_vital_signs_history'),
    path('patient_medical_history/', views.patient_medical_history, name='patient_medical_history'),
    path('view_treatment_plan/', views.view_treatment_plan_all, name='view_treatment_plan_all'),
    path('view_treatment_plan/<str:fname>/<str:lname>/<str:gender>/<str:bday>/', views.view_treatment_plan, name='view_treatment_plan'),
    path('patient_medication_doctor/', views.patient_medication_doctor, name='patient_medication_doctor'),
    path('patient_medication_table/', views.patient_medication_table, name = 'patient_medication_table'),
    path('outpatient_medication_order/', views.outpatient_medication_order, name = 'outpatient_medication_order'),
    path('save_prescriptions/', views.save_prescriptions, name = 'save_prescriptions'),
    path('perform_ocr/', views.perform_ocr, name='perform_ocr'),
    path('test/', views.pharmacy_drugs, name='pharmacy_drugs'),
    path('diagnostic_imagery_reports/read/<int:notification_id>/', views.diagnostic_imagery_reports, name="diagnostic_imagery_reports"),
    path('patient_personal_information_inpatient/', views.patient_personal_information_inpatient, name="patient_personal_information_inpatient"),
    path('save_chiefComplaint/', views.save_chiefComplaint, name="save_chiefComplaint"),
    path('save_review_of_systems/', views.save_review_of_systems, name='save_review_of_systems'),
    path('save_diagnosis/', views.save_diagnosis, name='save_diagnosis'),


    path('requestTest/', views.requestTest, name='requestTest'),

    path('newuser/', views.newuser, name='newuser'),
   
]