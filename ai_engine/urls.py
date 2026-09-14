from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ai_chatbot, name='ai_chatbot'),
    path('attendance/', views.ai_attendance_analytics, name='ai_attendance'),
    path('anomalies/', views.ai_payroll_anomaly, name='ai_anomalies'),
    path('risk/', views.ai_employee_risk, name='ai_risk'),
    path('salary-rec/', views.ai_salary_recommendations, name='ai_salary_rec'),
    path('report/', views.ai_natural_report, name='ai_report'),
]
