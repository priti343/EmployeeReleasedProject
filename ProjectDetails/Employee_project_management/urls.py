
from django.urls import path
from . import views

urlpatterns = [
    path('html/', views.emp_details, name='emp_details'),

    path('employee/<str:emp_id>/', views.employee_details, name='employee_details'),
    path('calculate_days_remaining/<str:emp_id>/', views.calculate_remaining_days_view, name='calculate_days_remaining'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('trigger-emails/', views.trigger_email_notifications, name='trigger_emails'),
    #path('test/', views.send_email_notification, name="test_email"),
]
