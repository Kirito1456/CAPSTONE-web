# forms.py
from django.forms import ModelForm
from django import forms
from hmis.models import Patient, Staff, AppointmentSchedule, Medications

class AppointmentScheduleForm(forms.ModelForm):
    DAYS_CHOICES = [
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    selected_days = forms.MultipleChoiceField(choices=DAYS_CHOICES, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = AppointmentSchedule
        fields = ('selected_days', 'morning_start', 'morning_end', 'afternoon_start', 'afternoon_end')

        labels = {
            'morning_start': 'Morning Start',
            'morning_end': 'Morning End',
            'afternoon_start': 'Afternoon Start',
            'afternoon_end': 'Afternoon End'
        }

        widgets = {
            'morning_start': forms.TimeInput(attrs={'class': 'timepicker'}),
            'morning_end': forms.TimeInput(attrs={'class': 'timepicker'}),
            'afternoon_start': forms.TimeInput(attrs={'class': 'timepicker'}),
            'afternoon_end': forms.TimeInput(attrs={'class': 'timepicker'})
        }

class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = Patient
        fields = ('fname', 'mname', 'lname', 'address', 'cnumber', 'birthday', 'email', 'password')
        
        labels = {
            'fname': 'First Name',
            'mname': 'Middle Name',
            'lname': 'Last Name',
            'address': 'Address',
            'cnumber': 'Contact Number',
            'birthday': 'Date of Birth',
            'email': 'Email',
            'password': 'Password',
        }

        widgets = {
            'fname': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'mname': forms.TextInput(attrs={'placeholder': 'Enter your middle name'}),
            'lname': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
            'cnumber': forms.TextInput(attrs={'placeholder': 'Enter your contact number'}),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }

class StaffRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirmpassword = forms.CharField(widget=forms.PasswordInput)
    
    # Define choices for sex and jobTitle fields
    SEX_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
    )

    ROLE_CHOICES = (
        ('Doctor', 'Doctor'),
        ('Nurse', 'Nurse'),
    )

    JOB_TITLE_CHOICES = (
        ('General Practitioner', 'General Practitioner'),
        ('Dermatologist', 'Dermatologist'),
        ('Pediatrician', 'Pediatrician'),
        ('Charge Nurse', 'Charge Nurse'),
        ('Bedside Nurse', 'Bedside Nurse'),
    )

    # DEPARTMENT_CHOICES = (
    #    ('General Ward', 'General Ward'),
    #)

    # Use forms.ChoiceField for sex and jobTitle fields
    sex = forms.ChoiceField(choices=SEX_CHOICES)
    specialization = forms.ChoiceField(choices=JOB_TITLE_CHOICES)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    #department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)

    class Meta:
        model = Staff
        fields = ('fname', 'lname', 'role', 'sex',   'specialization', 'email')
        widgets = {
            'fname': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'lname': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            #'clinic': forms.TextInput(attrs={'placeholder': 'Enter your clinic name'}),
            #'clinicaddress': forms.TextInput(attrs={'placeholder': 'Enter your clinic address'}),
        }

class MedicationsListForm(forms.ModelForm):
    
    ROUTE_CHOICES = (
        ('Oral', 'Oral'),
        ('Injection', 'Injection'),
        ('Topical', 'Topical'),
    )

    FREQUENCY_CHOICES = (
        ('Once Daily', 'Once Daily'),
        ('Twice Daily', 'Twice Daily'),
        ('Thrice Daily', 'Thrice Daily'),
    )

    route = forms.ChoiceField(choices=ROUTE_CHOICES)
    frequency = forms.ChoiceField(choices=FREQUENCY_CHOICES)

    class Meta:
        model = Medications
        fields = ('medicationname', 'dosage', 'route', 'frequency', 'additionalremarks')
        widgets = {
            'dosage': forms.TextInput(attrs={'placeholder': 'Enter Dosage'}),
            'additionalremarks': forms.EmailInput(attrs={'placeholder': 'Enter Remarks'}),
        }