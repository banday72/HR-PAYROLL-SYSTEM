from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class AuthorizedUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            if user.is_superuser:
                return user
            try:
                employee = user.employee
                if employee.status == 'active':
                    if employee.employee_id == 'CEO001':
                        return user
                    if (employee.department
                            and employee.department.name == 'Human Resources'
                            and employee.role in ('hr', 'manager')):
                        return user
            except Exception:
                pass
            return None
        return None
