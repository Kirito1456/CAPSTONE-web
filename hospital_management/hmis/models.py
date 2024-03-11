from django.db import models

# Create your models here.

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
    #cnumber = models.CharField(max_length=20, null=True)
    clinic = models.CharField(max_length=255, null=True)
    #clinicaddress = models.CharField(max_length=255, null=True)
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
    specialization = models.CharField(max_length=20, choices=JOB_TITLE_CHOICES)

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

class Appointment(models.Model):
    aDate = models.DateField()
    aTime = models.TimeField()
    aName = models.CharField(max_length=255)
    aVisitType = models.CharField(max_length=255, default='')
    aStatus = models.CharField(max_length=255)

    def __str__(self):
        return self.name  # or return self.email or any other field

class Details(models.Model):
    aEmail = models.EmailField(unique=True)
    aCNumber = models.IntegerField()
    aAddress = models.CharField(max_length=255)

    def __str__(self):
        return self.name  # or return self.email or any other field