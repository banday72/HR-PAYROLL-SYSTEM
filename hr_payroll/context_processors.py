def role_context(request):
    context = {'is_hr': False, 'current_employee': None}
    if request.user.is_authenticated:
        try:
            from employees.models import Employee
            emp = Employee.objects.get(user=request.user)
            context['current_employee'] = emp
            context['is_hr'] = emp.is_hr
        except Employee.DoesNotExist:
            if request.user.is_superuser:
                context['is_hr'] = True
    return context
