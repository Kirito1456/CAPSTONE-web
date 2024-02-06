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