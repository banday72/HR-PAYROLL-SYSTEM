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
                if not employee.is_authorized or employee.status != 'active':
                    return None
                if employee.role in ('hr', 'manager'):
                    return user
                if employee.role == 'employee' and employee.approved_by_manager:
                    return user
            except Exception:
                pass
            return None
        return None
