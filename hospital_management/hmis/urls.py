from django.urls import path
from hmis import views

urlpatterns = [
    path('', views.appointment, name='appointment'),
    path('AppointmentUpcoming.html', views.AppointmentUpcoming, name='AppointmentUpcoming'),
    path('AppointmentPast.html', views.AppointmentPast, name='AppointmentPast'),
    path('AppointmentCalendar.html', views.AppointmentCalendar, name='AppointmentCalendar'),
    path('Message.html', views.Message, name='Message'),
]