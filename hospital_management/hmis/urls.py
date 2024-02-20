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
]