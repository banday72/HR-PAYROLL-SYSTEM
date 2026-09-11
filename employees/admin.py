from django.contrib import admin
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'first_name', 'last_name', 'department', 'designation', 'salary', 'status', 'is_authorized']
    list_filter = ['status', 'department', 'gender', 'is_authorized']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
