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

    depts = {}
    for name, desc in [
        ('Human Resources', 'HR Department'),
        ('Engineering', 'Software development'),
        ('Finance', 'Financial planning'),
        ('Marketing', 'Brand and advertising'),
        ('Operations', 'Day-to-day operations'),
        ('Sales', 'Revenue generation'),
    ]:
        d, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
        depts[name] = d

    def get_or_create_emp(emp_id, first, last, email, dept_name, designation, salary, role='employee', reports_to=None, password='employee123'):
        if Employee.objects.filter(employee_id=emp_id).exists():
            return Employee.objects.get(employee_id=emp_id)
        user, _ = User.objects.get_or_create(username=emp_id,
            defaults={'email': email, 'first_name': first, 'last_name': last})
        user.set_password(password)
        user.save()
        emp = Employee.objects.create(
            employee_id=emp_id, first_name=first, last_name=last,
            email=email, department=depts.get(dept_name),
            designation=designation, date_of_joining=date(2021, 1, 1),
            salary=salary, status='active', role=role,
            is_authorized=True, approved_by_manager=True,
            reports_to=reports_to)
        emp.user = user
        emp.save()
        return emp

    # CEO
    ceo = get_or_create_emp('CEO001', 'Ahmed', 'Banday', 'ahmed.banday@company.com',
        'Operations', 'CEO', 500000, role='manager', password='ceo123')

    # HR Manager (reports to CEO)
    hm = get_or_create_emp('HM001', 'Fatima', 'Khan', 'hr.manager@company.com',
        'Human Resources', 'HR Manager', 150000, role='manager', reports_to=ceo, password='hm123')

    # Department Managers (report to CEO)
    mgr1 = get_or_create_emp('MGR001', 'Usman', 'Tariq', 'usman.tariq@company.com',
        'Finance', 'Finance Manager', 180000, role='manager', reports_to=ceo, password='manager123')
    mgr2 = get_or_create_emp('MGR002', 'Zainab', 'Ahmed', 'zainab.ahmed@company.com',
        'Engineering', 'Engineering Manager', 190000, role='manager', reports_to=ceo, password='manager123')
    mgr3 = get_or_create_emp('MGR003', 'Ayesha', 'Noor', 'ayesha.noor@company.com',
        'Operations', 'Operations Manager', 170000, role='manager', reports_to=ceo, password='manager123')
    mgr4 = get_or_create_emp('MGR004', 'Bilal', 'Sheikh', 'bilal.sheikh@company.com',
        'Sales', 'Sales Manager', 160000, role='manager', reports_to=ceo, password='manager123')

    # Employees (report to their managers)
    get_or_create_emp('EMP001', 'Ahmed', 'Khan', 'ahmed.khan@company.com',
        'Engineering', 'Senior Developer', 85000, reports_to=mgr2)
    get_or_create_emp('EMP002', 'Sara', 'Malik', 'sara.malik@company.com',
        'Human Resources', 'HR Executive', 70000, role='hr', reports_to=hm)
    get_or_create_emp('EMP003', 'Omar', 'Raza', 'omar.raza@company.com',
        'Finance', 'Financial Analyst', 75000, reports_to=mgr1)
    get_or_create_emp('EMP004', 'Hassan', 'Iqbal', 'hassan.iqbal@company.com',
        'Marketing', 'Marketing Lead', 72000, reports_to=mgr3)
    get_or_create_emp('EMP005', 'Fatima', 'Ali', 'fatima.ali@company.com',
        'Engineering', 'Full Stack Developer', 80000, reports_to=mgr2)
    get_or_create_emp('EMP006', 'Hamza', 'Tariq', 'hamza.tariq@company.com',
        'Operations', 'Operations Executive', 65000, reports_to=mgr3)
    get_or_create_emp('EMP007', 'Kamran', 'Shah', 'kamran.shah@company.com',
        'Sales', 'Sales Executive', 60000, reports_to=mgr4)
    get_or_create_emp('EMP008', 'Ali', 'Raza', 'ali.raza@company.com',
        'Engineering', 'DevOps Engineer', 82000, reports_to=mgr2)
    get_or_create_emp('EMP009', 'Bilal', 'Ahmed', 'bilal.ahmed@company.com',
        'Finance', 'Accountant', 62000, reports_to=mgr1)
    get_or_create_emp('EMP010', 'Hira', 'Shah', 'hira.shah@company.com',
        'Human Resources', 'HR Admin', 58000, reports_to=hm)

    # Auto-create public payslip link for EMP001
    from payroll.models import PublicPayrollLink
    emp001 = Employee.objects.filter(employee_id='EMP001').first()
    if emp001 and not PublicPayrollLink.objects.filter(employee=emp001).exists():
        PublicPayrollLink.objects.create(employee=emp001, is_active=True)
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
