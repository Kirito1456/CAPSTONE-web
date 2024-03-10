from django.urls import path
from hmis import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('reset/', views.reset , name='reset'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
    path('logout/', views.logout, name='logout'),
    path('Profile.html', views.profile, name='Profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('AppointmentUpcoming.html', views.AppointmentUpcoming, name='AppointmentUpcoming'),
    path('nursdashboard.html', views.NurseDashboard, name='NurseDashboard'),
    path('doctordashboard.html', views.DoctorDashboard, name='DoctorDashboard'),
    path('AppointmentPast.html', views.AppointmentPast, name='AppointmentPast'),
    path('AppointmentCalendar.html', views.AppointmentCalendar, name='AppointmentCalendar'),
    path('Message.html', views.Message, name='Message'),
    path('AppointmentCalendarRequestDetails.html', views.AppointmentCalendarRequestDetails, name='AppointmentCalendarRequestDetails'),
    path('delete_appointment/', views.delete_appointment, name='delete_appointment'),
    path('update_appointment/', views.update_appointment, name='update_appointment'),
]