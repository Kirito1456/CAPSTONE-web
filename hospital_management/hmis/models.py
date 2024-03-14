from django.db import models

# Create your models here.
class Prescription(models.Model):
    patient_id = models.CharField(max_length=100)
    medicine_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    additional_remarks = models.CharField(max_length=100)

class Medications(models.Model):
    uid = models.CharField(max_length=255, blank=True, null=True)
    medicationname = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    ROUTE_CHOICES = (
        ('Oral', 'Oral'),
        ('Injection', 'Injection'),
        ('Topical', 'Topical'),
    )
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES , null=True)
    FREQUENCY_CHOICES = (
        ('Once Daily', 'Once Daily'),
        ('Twice Daily', 'Twice Daily'),
        ('Thrice Daily', 'Thrice Daily'),
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES , null=True)
    additionalremarks = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Patient(models.Model):
    uid = models.CharField(max_length=255, blank=True, null=True)
    fname = models.CharField(max_length=255)
    mname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    cnumber = models.IntegerField()
    birthday = models.DateField()
    email = models.EmailField(unique=True)
    #password = models.CharField(max_length=255)

    def __str__(self):
        return self.name  # or return self.email or any other field

class Staff(models.Model):
    uid = models.CharField(max_length=255, blank=True, null=True)
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    cnumber = models.CharField(max_length=20)
    birthday = models.DateField()
    SEX_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
    )
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    JOB_TITLE_CHOICES = (
        ('General Practitioner', 'General Practitioner'),
        ('Dermatologist', 'Dermatologist'),
        ('Pediatrician', 'Pediatrician'),
        ('Head Nurse', 'Head Nurse'),
        ('Nurse Assistant', 'Nurse Assistant'),
    )
    jobTitle = models.CharField(max_length=20, choices=JOB_TITLE_CHOICES)

    ROLE_CHOICES = (
        ('Doctor', 'Doctor'),
        ('Nurse', 'Nurse'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES , null=True)
    DEPARTMENT_CHOICES = (
        ('General Ward', 'General Ward'),
    )
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, null=True)
    email = models.EmailField()

    def __str__(self):
        return self.name  # or return self.email or any other field
