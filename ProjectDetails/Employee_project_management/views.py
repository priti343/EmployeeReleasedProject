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
from collections import defaultdict

# Calculate remaining days function
def calculate_remaining_days(last_working_date):
    current_date = datetime.now().date()
    difference = current_date - last_working_date
    remaining_days = difference.days
    is_45_days_remaining = remaining_days == 45
    return remaining_days, is_45_days_remaining

# Group employees by PMO and TCC
def group_employees_by_pmo_tcc(employees):
    grouped_employees = defaultdict(list)
    for employee in employees:
        key = (employee.PMO_email, employee.Talent_central_contact_email)
        grouped_employees[key].append(employee)
    return grouped_employees

# Send email notification function with grey header styling
def send_email_notification(grouped_employees):
    sender_email = settings.EMAIL_HOST_USER

    for (pmo_email, tcc_email), employees in grouped_employees.items():
        recipients = [pmo_email, tcc_email]
        subject = 'Employees with 45 Days Since Release'

        message = """
        <html>
        <head>
            <style>
                body {
                    color: black; /* Default text color */
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid grey;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: grey; /* Header background color */
                    color: white; /* Header text color */
                }
            </style>
        </head>
        <body>
        Hello,<br><br>
        I hope this email finds you well.<br><br>
        The following members have been release from the project since 45 days, I request you to please take some actions.<br><br>
        <table>
            <tr>
                <th>Employee ID</th>
                <th>Name</th>
                <th>Project Name</th>
                <th>Last Working Date</th>
                <th>Reporting Manager ID</th>
                <th>Reporting Manager Name</th>
                <th>Project Released Feedback</th>
            </tr>
        """

        for employee in employees:
            message += f"""
            <tr>
                <td>{employee.Emp_id}</td>
                <td>{employee.Emp_name}</td>
                <td>{employee.Project_name}</td>
                <td>{employee.Last_working_date}</td>
                <td>{employee.Reporting_manager_id}</td>
                <td>{employee.Reporting_manager_name}</td>
                <td>{employee.Project_released_feedback}</td>
            </tr>
            """

        message += """
        </table>
        <br>Regards,<br>Your Company
        </body>
        </html>
        """

        email = MIMEMultipart()
        email['From'] = sender_email
        email['To'] = ', '.join(recipients)
        email['Subject'] = subject
        email.attach(MIMEText(message, 'html'))

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as smtp_server:
            smtp_server.starttls()
            smtp_server.login(sender_email, settings.EMAIL_HOST_PASSWORD)
            smtp_server.send_message(email)

        #log_email(sender_email, recipients, subject, message)

# View to display employee details and check if an email notification needs to be sent
def employee_details(request, emp_id):
    try:
        employee = EmployeeDetails.objects.get(Emp_id=emp_id)
        remaining_days, is_45_days_remaining = calculate_remaining_days(employee.Last_working_date)
        if is_45_days_remaining:
            send_email_notification({(employee.PMO_email, employee.Talent_central_contact_email): [employee]})
        context = {'employee': employee, 'remaining_days': remaining_days}
        return render(request, 'employee_details.html', context)
    except EmployeeDetails.DoesNotExist:
        return HttpResponse("Employee not found!")

# Simple employee details view
def emp_details(request):
    return render(request, 'employee_details.html')

# View to calculate remaining days for a specific employee
def calculate_remaining_days_view(request, emp_id):
    try:
        employee = EmployeeDetails.objects.get(Emp_id=emp_id)
        remaining_days, _ = calculate_remaining_days(employee.Last_working_date)
        return HttpResponse(f"Remaining days for employee {emp_id}: {remaining_days}")
    except EmployeeDetails.DoesNotExist:
        return HttpResponse("Employee not found!")

# Decorator for validating Excel file uploads
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

            for index, row in df.iterrows():
                try:
                    employee = EmployeeDetails.objects.get(Emp_id=row['Emp_id'])
                    employee.Emp_name = row['Emp_name']
                    employee.Project_name = row['Project_name']
                    employee.Last_working_date = row['Last_working_date']
                    employee.Reporting_manager_id = row['Reporting_manager_id']
                    employee.Reporting_manager_name = row['Reporting_manager_name']
                    employee.Project_released_feedback = row['Project_released_feedback']
                    employee.PMO = row['PMO']
                    employee.PMO_name = row['PMO_name']
                    employee.PMO_email = row['PMO_email']
                    employee.Talent_central_contact_name = row['Talent_central_contact_name']
                    employee.Talent_central_contact_email = row['Talent_central_contact_email']
                    employee.save()
                except EmployeeDetails.DoesNotExist:
                    EmployeeDetails.objects.create(
                        Emp_id=row['Emp_id'],
                        Emp_name=row['Emp_name'],
                        Project_name=row['Project_name'],
                        Last_working_date=row['Last_working_date'],
                        Reporting_manager_id=row['Reporting_manager_id'],
                        Reporting_manager_name=row['Reporting_manager_name'],
                        Project_released_feedback=row['Project_released_feedback'],
                        PMO=row['PMO'],
                        PMO_name=row['PMO_name'],
                        PMO_email=row['PMO_email'],
                        Talent_central_contact_name=row['Talent_central_contact_name'],
                        Talent_central_contact_email=row['Talent_central_contact_email']
                    )

            return render(request, 'success.html')
    else:
        form = ExcelUploadForm()
    return render(request, 'upload_excel.html', {'form': form})

def trigger_email_notifications(request):
    forty_five_days_ago = timezone.now().date() - timedelta(days=45)
    employees = EmployeeDetails.objects.filter(Last_working_date=forty_five_days_ago)
    grouped_employees = group_employees_by_pmo_tcc(employees)
    send_email_notification(grouped_employees)
    return HttpResponse("Email notifications triggered successfully.")
