from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def hr_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from .models import Employee
        try:
            employee = Employee.objects.select_related('department').get(user=request.user)
            if employee.is_hr:
                return view_func(request, *args, **kwargs)
        except Employee.DoesNotExist:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. HR privileges required.')
        return redirect('dashboard')
    return wrapper


def privilege_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from .models import Employee
        try:
            employee = Employee.objects.select_related('department').get(user=request.user)
            if employee.role in ('hr', 'manager') or employee.is_chief:
                return view_func(request, *args, **kwargs)
        except Employee.DoesNotExist:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        messages.error(request, 'Access denied. Granting login access is limited to HR and Management.')
        return redirect('dashboard')
    return wrapper
