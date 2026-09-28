def role_context(request):
    context = {'is_hr': False, 'current_employee': None, 'ceo_employee': None, 'current_manager': None, 'unread_notif_count': 0}
    if request.user.is_authenticated:
        from employees.models import Employee

        try:
            ceo = Employee.objects.get(employee_id='CEO001')
            context['ceo_employee'] = ceo
        except Exception:
            pass

        try:
            emp = Employee.objects.get(user=request.user)
            context['current_employee'] = emp
            context['is_hr'] = emp.is_hr or emp.employee_id == 'CEO001'
            if emp.reports_to:
                context['current_manager'] = emp.reports_to
        except Employee.DoesNotExist:
            if request.user.is_superuser:
                context['is_hr'] = True

        try:
            from hr_modules.models import Notification
            if context.get('current_employee'):
                context['unread_notif_count'] = Notification.objects.filter(employee=context['current_employee'], is_read=False).count()
            elif request.user.is_superuser:
                context['unread_notif_count'] = Notification.objects.filter(is_read=False).count()
        except Exception:
            pass
    return context
