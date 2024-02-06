# forms.py
from django.forms import ModelForm
from django import forms
from hmis.models import Patient

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
