def role_context(request):
    context = {'is_hr': False, 'current_employee': None, 'ceo_employee': None, 'is_ceo_readonly': False}
    if request.user.is_authenticated:
        from employees.models import Employee

        try:
            ceo = Employee.objects.get(employee_id='CEO001')
            context['ceo_employee'] = ceo
        except Employee.DoesNotExist:
            pass

        try:
            emp = Employee.objects.get(user=request.user)
            context['current_employee'] = emp
            context['is_hr'] = emp.is_hr or emp.employee_id == 'CEO001'
            if emp.employee_id == 'CEO001':
                context['is_ceo_readonly'] = True
                context['is_hr'] = True
        except Employee.DoesNotExist:
            if request.user.is_superuser:
                context['is_hr'] = True
    return context
