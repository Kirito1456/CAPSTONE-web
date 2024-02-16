from django.db import models

# Create your models here.

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