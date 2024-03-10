from django.urls import path
from hmis import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('reset/', views.reset , name='reset'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
    path('patient_data_doctor_view/', views.patient_data_doctor_view, name='patient_data_doctor_view'),
    path('patient_personal_information/', views.patient_personal_information, name='patient_personal_information'),
    path('new_vital_sign_entry/', views.new_vital_sign_entry, name='new_vital_sign_entry'),
    path('patient_medical_history/', views.patient_medical_history, name='patient_medical_history'),
    path('view_treatment_plan/', views.view_treatment_plan, name='view_treatment_plan'),
    path('view_treatment_plan/<str:fname>/<str:lname>/<str:gender>/<str:bday>/', views.view_treatment_plan, name='view_treatment_plan'),
    path('patient_medication_doctor/', views.patient_medication_doctor, name='patient_medication_doctor'),
    path('patient_medication_nurse/', views.patient_medication_nurse, name='patient_medication_nurse'),
    path('patient_medication_table/', views.patient_medication_table, name = 'patient_medication_table'),
    path('patient_medication_table/<str:fname>/<str:lname>/<str:gender>/<str:bday>/', views.patient_medication_table, name='patient_medication_table'),
    path('outpatient_medication_order/', views.outpatient_medication_order, name = 'outpatient_medication_order'),
    path('inpatient_medication_order/', views.inpatient_medication_order, name = 'inpatient_medication_order'),
    path('perform_ocr/', views.perform_ocr, name='perform_ocr'),
    path('test/', views.pharmacy_drugs, name='pharmacy_drugs'),
    path('diagnostic_lab_reports/', views.diagnostic_lab_reports, name='diagnostic_lab_reports'),
    path('diagnostic_imagery_reports/', views.diagnostic_imagery_reports, name="diagnostic_imagery_reports"),
    path('patient_personal_information_inpatient/', views.patient_personal_information_inpatient, name="patient_personal_information_inpatient"),
]