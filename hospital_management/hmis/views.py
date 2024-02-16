# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages

def appointment(request):
    return render(request, 'hmis/AppointmentUpcoming.html')

def AppointmentUpcoming(request):
    return render(request, 'hmis/AppointmentUpcoming.html')
 
def AppointmentPast(request):
    return render(request, 'hmis/AppointmentPast.html')

def AppointmentCalendar(request):
    return render(request, 'hmis/AppointmentCalendar.html')

def Message(request):
    return render(request, 'hmis/Message.html')