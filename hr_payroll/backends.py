from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class AuthorizedUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None
        if user.is_superuser:
            return user

        from employees.models import MANAGEMENT_DEPARTMENT_NAMES, is_chief_designation
        try:
            employee = user.employee
            if employee.status != 'active':
                return None
            if employee.employee_id == 'CEO001':
                return user
            if is_chief_designation(employee.designation):
                return user
            if employee.department and employee.role in ('hr', 'manager'):
                if employee.department.name == 'Human Resources':
                    return user
                if employee.department.name.strip().lower() in MANAGEMENT_DEPARTMENT_NAMES:
                    return user
        except Exception:
            pass
        return None
