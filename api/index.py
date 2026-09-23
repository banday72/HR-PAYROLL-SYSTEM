import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')

import django
django.setup()

from django.core.management import call_command
try:
    call_command('migrate', '--run-syncdb', '--noinput', verbosity=0)
except Exception:
    pass

try:
    from django.contrib.auth.models import User
    from employees.models import Employee, Department
    from datetime import date

    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@hrpayroll.com', 'admin123')

    if not User.objects.filter(username='CEO001').exists():
        ceo_user = User.objects.create_user('CEO001', 'ahmed.banday@company.com', 'ceo123',
            first_name='Ahmed', last_name='Banday')
        ceo_emp = Employee.objects.create(
            employee_id='CEO001', first_name='Ahmed', last_name='Banday',
            email='ahmed.banday@company.com', date_of_joining=date.today(),
            salary=500000, status='active', role='manager',
            designation='Manager', is_authorized=True, approved_by_manager=True)
        ceo_emp.user = ceo_user
        ceo_emp.save()

    if not User.objects.filter(username='HM001').exists():
        hr_dept, _ = Department.objects.get_or_create(name='Human Resources',
            defaults={'description': 'HR Department'})
        hm_user = User.objects.create_user('HM001', 'hr.manager@company.com', 'hm123',
            first_name='HR', last_name='Manager')
        hm_emp = Employee.objects.create(
            employee_id='HM001', first_name='HR', last_name='Manager',
            email='hr.manager@company.com', department=hr_dept,
            designation='HR Manager', date_of_joining=date(2022, 1, 1),
            salary=150000, status='active', role='manager',
            is_authorized=True, approved_by_manager=True)
        hm_emp.user = hm_user
        hm_emp.save()
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

def handler(request):
    status_code = 200
    headers_dict = {}

    def start_response(status, headers, exc_info=None):
        nonlocal status_code, headers_dict
        status_code = int(status.split(' ', 1)[0])
        headers_dict = dict(headers)

    response_body = b''.join(application(request.environ, start_response))

    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': response_body.decode('utf-8', errors='replace'),
    }
