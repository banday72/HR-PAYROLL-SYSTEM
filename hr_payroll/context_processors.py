class SuperadminProfile:
    def __init__(self, user):
        self.user = user
        self.profile_picture = None
        self.designation = 'Administrator'
        self.role = 'superadmin'
        self.is_hr = True
        self.is_manager = True

    @property
    def is_hr(self):
        return True

    @property
    def is_manager(self):
        return True


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
                context['current_employee'] = SuperadminProfile(request.user)
    return context
