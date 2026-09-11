from django.contrib import admin
from .models import Department, Employee, AuditLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'first_name', 'last_name', 'department', 'designation', 'salary', 'status', 'is_authorized', 'approved_by_manager', 'role']
    list_filter = ['status', 'department', 'gender', 'is_authorized', 'approved_by_manager', 'role']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['description', 'object_id']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp']
