from django.shortcuts import render
from django.http import HttpResponse
from .models import EmployeeDetails
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from .forms import ExcelUploadForm
from django.utils import timezone
from django.conf import settings



def calculate_remaining_days(last_working_date):
    current_date = datetime.now().date()
    difference = last_working_date - current_date
    remaining_days = abs(difference.days)
    is_45_days_remaining = remaining_days == 45
    return remaining_days, is_45_days_remaining
#check if the difference is exactly 45 is_45_days_remaining
    if is_45_days_remaining:
        return remaining_days, True
    return remaining_days, False
def logEmail(sender_email, recipients, subject, message):
    try:
        print("Inside the LogEmail Method.")
        with open("email.log", "a") as f:
            _str = f'Sender : {sender_email}, recipients : {recipients} , Subject : {subject}, Message : {message}\n'
            f.write(_str)
            f.write("-----------------------------------------------\n")
    except ex:
        print(ex)

def send_email_notification(employee):
    sender_email = settings.EMAIL_HOST_USER
    recipients = [employee.PMO_email, employee.Talent_central_contact_email]
    subject = f'{employee.Emp_id} - {employee.Emp_name}'
    message = f'Hello,<br>\n\n'
    message += f'Hello,<br>\n\nI hope this email finds you well.<br>\n\nThe following members have been released from the project since 45 days, I request you to please take some actions.\n\n<br><br>'

    message += f'<table border="1"><tr><th>Employee ID</th><th>Name</th><th>Project Name</th><th>Last Working Date</th><th>Reporting Manager ID</th><th>Reporting Manage Name</th><th>Project Released Feedback</th></tr>'
    message += f'<tr><td>{employee.Emp_id}</td><td>{employee.Emp_name}</td><td>{employee.Project_name}</td><td>{employee.Last_working_date}</td><td>{employee.Reporting_manager_id}</td><td>{employee.Reporting_manager_name}</td><td>{employee.Project_released_feedback}</td></tr></table>'
    message += '\n\nRegards,\nYour Company'


    email = MIMEMultipart()
    email['From'] = sender_email
    email['To'] = ', '.join(recipients)
    email['Subject'] = subject
    email['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    email.attach(MIMEText(message, 'html'))
    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(sender_email, settings.EMAIL_HOST_PASSWORD)
            smtp_server.send_message(email)


def employee_details(request, emp_id):
    try:
        employee = EmployeeDetails.objects.get(Emp_id=emp_id)
        remaining_days, is_45_days_remaining = calculate_remaining_days(employee.Last_working_date)
        if is_45_days_remaining:
            send_email_notification(employee)
        context = {'employee': employee, 'remaining_days': remaining_days}
        return render(request, 'employee_details.html', context)
    except EmployeeDetails.DoesNotExist:
        return HttpResponse("Employee not found!")


def emp_details(request):
    return render(request, 'employee_details.html')


def calculate_remaining_days_view(request, emp_id):
    try:
        employee = EmployeeDetails.objects.get(Emp_id=emp_id)
        remaining_days = calculate_remaining_days(employee.Last_working_date)
        return HttpResponse(f"Remaining days for employee {emp_id}: {remaining_days}")
    except EmployeeDetails.DoesNotExist:
        return HttpResponse("Employee not found!")


def validate_excel(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                return view_func(request, *args, **kwargs)
        else:
            form = ExcelUploadForm()
        return render(request, 'upload_excel.html', {'form': form})
    return wrapper


@validate_excel
def upload_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            for index, column in df.iterrows():
                # Check if EmployeeDetails with same Emp_id exists
                try:
                    employee = EmployeeDetails.objects.get(Emp_id=column['Emp_id'])

                    # If EmployeeDetails with same Emp_id exists, update its details
                    employee.Emp_name = column['Emp_name']
                    employee.Project_name = column['Project_name']
                    employee.Last_working_date = column['Last_working_date']
                    employee.Reporting_manager_id = column['Reporting_manager_id']
                    employee.Reporting_manager_name = column['Reporting_manager_name']
                    employee.Project_released_feedback = column['Project_released_feedback']
                    employee.PMO = column['PMO']
                    employee.PMO_name = column['PMO_name']
                    employee.PMO_email = column['PMO_email']
                    employee.Talent_central_contact_name = column['Talent_central_contact_name']
                    employee.Talent_central_contact_email = column['Talent_central_contact_email']
                    employee.save()

                # If EmployeeDetails with same Emp_id doesn't exist, create a new one
                except EmployeeDetails.DoesNotExist:
                    EmployeeDetails.objects.create(
                        Emp_id=column['Emp_id'],
                        Emp_name=column['Emp_name'],
                        Project_name=column['Project_name'],
                        Last_working_date=column['Last_working_date'],
                        Reporting_manager_id=column['Reporting_manager_id'],
                        Reporting_manager_name=column['Reporting_manager_name'],
                        Project_released_feedback=column['Project_released_feedback'],
                        PMO=column['PMO'],
                        PMO_name=column['PMO_name'],
                        PMO_email=column['PMO_email'],
                        Talent_central_contact_name=column['Talent_central_contact_name'],
                        Talent_central_contact_email=column['Talent_central_contact_email']
                    )

            return render(request, 'success.html')

    else:
        form = ExcelUploadForm()

    return render(request, 'upload_excel.html', {'form': form})


def trigger_email_notifications(request):

    forty_five_days_ago = timezone.now() - timedelta(days=45) # Calculate the date which is 45 days before the current date
    employees = EmployeeDetails.objects.filter(Last_working_date=forty_five_days_ago)
     #Fetch employees whose last working date is 45 days
    for employee in employees: #Iterate only the filtered employees and send email notifications
        send_email_notification(employee)

    return HttpResponse("Email notifications triggered successfully.")
