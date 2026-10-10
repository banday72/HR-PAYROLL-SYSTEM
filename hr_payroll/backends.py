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

        from employees.models import Employee
        try:
            employee = user.employee
            if employee.status == 'active':
                return user
        except Employee.DoesNotExist:
            pass
        return None
