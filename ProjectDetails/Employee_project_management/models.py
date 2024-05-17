from django.db import models

# Create your models here.


class EmployeeDetails(models.Model):
    Emp_id = models.CharField(max_length=100)
    Emp_name = models.CharField(max_length=255)
    Project_name = models.CharField(max_length=255)
    Last_working_date = models.DateField()
    Reporting_manager_id = models.CharField(max_length=100)
    Reporting_manager_name = models.CharField(max_length=255)
    Project_released_feedback = models.TextField()
    PMO = models.CharField(max_length=255)
    PMO_name = models.CharField(max_length=255)
    PMO_email = models.EmailField()
    Talent_central_contact_name = models.CharField(max_length=255)
    Talent_central_contact_email = models.EmailField()

    def __str__(self):
        return f"{self.Emp_id} - {self.Emp_name}"
