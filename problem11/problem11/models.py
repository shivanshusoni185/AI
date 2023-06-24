from django.db import models

class Student(models.Model):
    AdmissionionID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100)
    DataOfBirth = models.DateField()
    Gender = models.CharField(max_length=10)
    Address = models.CharField(max_length=200)
    AdmissionDate = models.DateField()

    def __str__(self):
        return self.Name
