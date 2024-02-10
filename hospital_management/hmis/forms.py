# forms.py
from django.forms import ModelForm
from django import forms
from hmis.models import Patient, Staff

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
        ('Head Nurse', 'Head Nurse'),
        ('Nurse Assistant', 'Nurse Assistant'),
    )

    DEPARTMENT_CHOICES = (
        ('General Ward', 'General Ward'),
    )

    # Use forms.ChoiceField for sex and jobTitle fields
    sex = forms.ChoiceField(choices=SEX_CHOICES)
    jobTitle = forms.ChoiceField(choices=JOB_TITLE_CHOICES)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES)

    class Meta:
        model = Staff
        fields = ('fname', 'lname', 'cnumber', 'birthday', 'sex', 'department', 'jobTitle', 'email')
        widgets = {
            'fname': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'lname': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'cnumber': forms.TextInput(attrs={'placeholder': 'Enter your contact number'}),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }