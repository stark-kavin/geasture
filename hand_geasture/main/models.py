from django.db import models
from django.contrib.auth.models import User


class UserProfiles(models.Model):
    ROLES = [('doctor', 'Doctor'), ('nurse', 'Nurse'), ('admin', 'Admin')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLES) 
    password_last_changed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
class Patient(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    password = models.CharField(max_length=128)
    alert = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class PatientLink(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient')
    account = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name='account')

    def __str__(self):
        return f"{self.account.user.username} - {self.patient.name}"