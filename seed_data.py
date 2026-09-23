import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from employees.models import Department, Employee
from attendance.models import Attendance
from leaves.models import LeaveType, Leave
from payroll.models import Payroll, PayrollPolicy, BoutiqueProduct, BoutiqueIssue, BudgetLoan
from datetime import date, time, timedelta
import calendar

print("Seeding database...")

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@hrpayroll.com', 'admin123')
    print("Created superuser: admin / admin123")

# Create departments
departments_data = [
    ('Human Resources', 'Manages recruitment, employee relations, and benefits'),
    ('Engineering', 'Software development and technical operations'),
    ('Finance', 'Financial planning, accounting, and budgeting'),
    ('Marketing', 'Brand management, advertising, and market research'),
    ('Operations', 'Day-to-day business operations and logistics'),
    ('Sales', 'Client acquisition and revenue generation'),
]
departments = {}
for name, desc in departments_data:
    dept, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
    departments[name] = dept
print(f"Created {len(departments)} departments")

# Create CEO
ceo_emp = None
if not Employee.objects.filter(employee_id='CEO001').exists():
    ceo_user, _ = User.objects.get_or_create(username='CEO001',
        defaults={'email': 'ahmed.banday@company.com', 'first_name': 'Ahmed', 'last_name': 'Banday'})
    ceo_user.set_password('ceo123')
    ceo_user.save()
    ceo_emp = Employee.objects.create(
        employee_id='CEO001', first_name='Ahmed', last_name='Banday',
        email='ahmed.banday@company.com', phone='0300-0000000',
        designation='CEO', date_of_joining=date(2020, 1, 1),
        salary=500000, status='active', role='manager',
        is_authorized=True, approved_by_manager=True)
    ceo_emp.user = ceo_user
    ceo_emp.save()
    print("Created CEO: CEO001 / ceo123")
else:
    ceo_emp = Employee.objects.get(employee_id='CEO001')

# Level 2: Department Managers (report to CEO)
managers_data = [
    ('MGR001', 'Usman', 'Tariq', 'usman.tariq@company.com', 'M', 'Finance', 'Finance Manager', 180000),
    ('MGR002', 'Zainab', 'Ahmed', 'zainab.ahmed@company.com', 'F', 'Engineering', 'Engineering Manager', 190000),
    ('MGR003', 'Ayesha', 'Noor', 'ayesha.noor@company.com', 'F', 'Operations', 'Operations Manager', 170000),
    ('MGR004', 'Bilal', 'Sheikh', 'bilal.sheikh@company.com', 'M', 'Sales', 'Sales Manager', 160000),
]

managers = {}
for emp_id, first, last, email, gender, dept_name, designation, salary in managers_data:
    emp, created = Employee.objects.get_or_create(
        employee_id=emp_id,
        defaults={
            'first_name': first, 'last_name': last, 'email': email, 'gender': gender,
            'department': departments[dept_name], 'designation': designation,
            'date_of_joining': date(2021, 6, 1), 'salary': salary,
            'status': 'active', 'role': 'manager', 'is_authorized': True,
            'approved_by_manager': True, 'reports_to': ceo_emp,
        }
    )
    if not emp.user:
        user, uc = User.objects.get_or_create(username=emp_id,
            defaults={'email': email, 'first_name': first, 'last_name': last})
        if uc:
            user.set_password('manager123')
            user.save()
        emp.user = user
        emp.save()
    managers[emp_id] = emp
print(f"Created {len(managers)} department managers")

# HR Manager (reports to CEO)
hm_emp = None
if not Employee.objects.filter(employee_id='HM001').exists():
    hm_user, _ = User.objects.get_or_create(username='HM001',
        defaults={'email': 'hr.manager@company.com', 'first_name': 'Fatima', 'last_name': 'Khan'})
    hm_user.set_password('hm123')
    hm_user.save()
    hm_emp = Employee.objects.create(
        employee_id='HM001', first_name='Fatima', last_name='Khan',
        email='hr.manager@company.com', phone='0300-1234567',
        department=departments['Human Resources'], designation='HR Manager',
        date_of_joining=date(2021, 3, 1), salary=150000, status='active',
        role='manager', is_authorized=True, approved_by_manager=True,
        reports_to=ceo_emp)
    hm_emp.user = hm_user
    hm_emp.save()
    print("Created HR Manager: HM001 / hm123")
else:
    hm_emp = Employee.objects.get(employee_id='HM001')

# Level 3: Employees (report to their respective managers)
employees_data = [
    ('EMP001', 'Ahmed', 'Khan', 'ahmed.khan@company.com', 'M', 'Engineering', 'Senior Developer', 85000, 'MGR002'),
    ('EMP002', 'Sara', 'Malik', 'sara.malik@company.com', 'F', 'Human Resources', 'HR Executive', 70000, 'HM001'),
    ('EMP003', 'Omar', 'Raza', 'omar.raza@company.com', 'M', 'Finance', 'Financial Analyst', 75000, 'MGR001'),
    ('EMP004', 'Hassan', 'Iqbal', 'hassan.iqbal@company.com', 'M', 'Marketing', 'Marketing Lead', 72000, 'MGR003'),
    ('EMP005', 'Fatima', 'Ali', 'fatima.ali@company.com', 'F', 'Engineering', 'Full Stack Developer', 80000, 'MGR002'),
    ('EMP006', 'Hamza', 'Tariq', 'hamza.tariq@company.com', 'M', 'Operations', 'Operations Executive', 65000, 'MGR003'),
    ('EMP007', 'Kamran', 'Shah', 'kamran.shah@company.com', 'M', 'Sales', 'Sales Executive', 60000, 'MGR004'),
    ('EMP008', 'Ali', 'Raza', 'ali.raza@company.com', 'M', 'Engineering', 'DevOps Engineer', 82000, 'MGR002'),
    ('EMP009', 'Bilal', 'Ahmed', 'bilal.ahmed@company.com', 'M', 'Finance', 'Accountant', 62000, 'MGR001'),
    ('EMP010', 'Hira', 'Shah', 'hira.shah@company.com', 'F', 'Human Resources', 'HR Admin', 58000, 'HM001'),
]

employees = {}
for emp_id, first, last, email, gender, dept_name, designation, salary, mgr_id in employees_data:
    mgr = managers.get(mgr_id) or (hm_emp if mgr_id == 'HM001' else ceo_emp)
    emp, created = Employee.objects.get_or_create(
        employee_id=emp_id,
        defaults={
            'first_name': first, 'last_name': last, 'email': email, 'gender': gender,
            'department': departments[dept_name], 'designation': designation,
            'date_of_joining': date(2023, 1, 15), 'salary': salary,
            'status': 'active', 'is_authorized': True,
            'role': 'hr' if dept_name == 'Human Resources' and designation == 'HR Executive' else 'employee',
            'reports_to': mgr,
        }
    )
    if not emp.user:
        user, uc = User.objects.get_or_create(username=emp_id,
            defaults={'email': email, 'first_name': first, 'last_name': last})
        if uc:
            user.set_password('employee123')
            user.save()
        emp.user = user
        emp.save()
    employees[emp_id] = emp
print(f"Created {len(employees)} employees")

# Create leave types
leave_types_data = [
    ('Annual Leave', 20, 'Yearly vacation leave'),
    ('Sick Leave', 10, 'Medical leave'),
    ('Personal Leave', 5, 'Personal reasons'),
    ('Maternity Leave', 90, 'Maternity/paternity leave'),
]
leave_types = {}
for name, days, desc in leave_types_data:
    lt, _ = LeaveType.objects.get_or_create(name=name, defaults={'days_per_year': days, 'description': desc})
    leave_types[name] = lt
print(f"Created {len(leave_types)} leave types")

# Create attendance records
today = date(2026, 9, 8)
patterns = {
    'EMP001': ['present'] * 5 + ['late'] * 1 + ['present'],
    'EMP002': ['present'] * 4 + ['half_day'] * 1 + ['present'] * 2,
    'EMP003': ['present'] * 3 + ['absent'] * 1 + ['present'] * 2 + ['late'],
    'EMP004': ['present'] * 5 + ['holiday'] + ['present'],
    'EMP005': ['present'] * 6 + ['half_day'],
    'EMP006': ['present'] * 4 + ['late'] * 2 + ['present'],
    'EMP007': ['present'] * 3 + ['absent'] * 2 + ['present'] * 2,
    'EMP008': ['present'] * 5 + ['present'] * 2,
    'EMP009': ['present'] * 4 + ['half_day'] + ['late'] + ['present'],
    'EMP010': ['present'] * 2 + ['absent'] * 1 + ['present'] * 2 + ['half_day'] + ['present'],
}
for emp_id, emp in employees.items():
    pattern = patterns.get(emp_id, ['present'] * 7)
    for i in range(7):
        att_date = today - timedelta(days=i)
        status = pattern[i % len(pattern)]
        clock_in_time = time(9, 0) if status != 'absent' else None
        if status == 'late':
            import random
            clock_in_time = time(9, random.randint(15, 45))
        clock_out_time = time(17, 30) if status in ['present', 'late', 'half_day'] else None
        Attendance.objects.get_or_create(
            employee=emp, date=att_date,
            defaults={'clock_in': clock_in_time, 'clock_out': clock_out_time, 'status': status})
print("Created attendance records")

# Create leave requests
Leave.objects.get_or_create(
    employee=employees['EMP001'], leave_type=leave_types['Annual Leave'],
    start_date=date(2026, 9, 15), end_date=date(2026, 9, 20),
    defaults={'reason': 'Family vacation', 'status': 'approved', 'approved_by': 'Admin'})
Leave.objects.get_or_create(
    employee=employees['EMP003'], leave_type=leave_types['Sick Leave'],
    start_date=date(2026, 9, 10), end_date=date(2026, 9, 11),
    defaults={'reason': 'Medical appointment', 'status': 'pending'})
Leave.objects.get_or_create(
    employee=employees['EMP007'], leave_type=leave_types['Personal Leave'],
    start_date=date(2026, 9, 12), end_date=date(2026, 9, 12),
    defaults={'reason': 'Personal work', 'status': 'approved', 'approved_by': 'Admin'})
print("Created leave requests")

# Create payroll policy
PayrollPolicy.objects.get_or_create(
    name='Standard Company Policy',
    defaults={
        'working_days_per_month': 30, 'absent_deduction_per_day': 0,
        'use_per_day_salary_for_absent': True, 'half_day_deduction_percent': 50,
        'late_allowed_per_month': 3, 'late_deduction_amount': 500,
        'approved_leave_paid': True, 'tax_rate_percent': 10,
        'performance_bonus_enabled': True, 'bonus_100_percent': 10,
        'bonus_95_percent': 5, 'bonus_90_percent': 2, 'bonus_below_90_percent': 0,
        'medical_allowance': 5000, 'transport_allowance': 3000,
        'house_allowance_percent': 20, 'is_active': True})
print("Created payroll policy")

# Create payroll records
all_emps = list(employees.values())
for emp in all_emps:
    basic = emp.salary / 12
    allowances = basic * Decimal('0.15')
    deductions = basic * Decimal('0.05')
    tax = basic * Decimal('0.10')
    net = basic + allowances - deductions - tax
    Payroll.objects.get_or_create(
        employee=emp, month=8, year=2026,
        defaults={
            'basic_salary': round(basic, 2), 'allowances': round(allowances, 2),
            'deductions': round(deductions, 2), 'tax': round(tax, 2),
            'net_salary': round(net, 2), 'status': 'paid',
            'payment_date': date(2026, 8, 28), 'generated_type': 'auto'})
print("Created payroll records")

# Create boutique products
products_data = [
    ('Laptop', 80000, 10, 'Company laptop'),
    ('Office Chair', 15000, 20, 'Ergonomic chair'),
    ('Monitor', 35000, 15, 'External monitor'),
    ('Shirt', 1500, 100, 'Office uniform shirt'),
    ('Bag', 2500, 50, 'Laptop bag'),
]
products = {}
for name, price, stock, desc in products_data:
    p, _ = BoutiqueProduct.objects.get_or_create(name=name, defaults={'price': price, 'stock': stock, 'description': desc})
    products[name] = p
print(f"Created {len(products)} boutique products")

# Create boutique issues
issues_data = [
    ('EMP001', 'Laptop', 1, date(2026, 9, 1)),
    ('EMP003', 'Office Chair', 1, date(2026, 9, 3)),
    ('EMP005', 'Monitor', 1, date(2026, 9, 5)),
]
for emp_id, product_name, qty, issue_date in issues_data:
    prod = products[product_name]
    BoutiqueIssue.objects.get_or_create(
        employee=employees[emp_id], product=prod,
        defaults={'quantity': qty, 'total_price': prod.price * qty,
                  'issue_date': issue_date, 'is_deducted': False, 'issued_by': 'HR Manager'})
print("Created boutique issues")

# Create budget loans
loan_data = [
    ('EMP001', 60000, 5000, 'Emergency loan', date(2026, 8, 1)),
    ('EMP004', 30000, 3000, 'Advance salary', date(2026, 7, 1)),
]
for emp_id, loan_amount, monthly, reason, start_date in loan_data:
    BudgetLoan.objects.get_or_create(
        employee=employees[emp_id], reason=reason,
        defaults={'loan_amount': loan_amount, 'monthly_deduction': monthly,
                  'start_date': start_date, 'is_active': True,
                  'total_deducted': 0, 'remaining_amount': loan_amount})
print("Created budget loans")

# Print hierarchy
print("\n" + "=" * 60)
print("ORGANIZATION HIERARCHY")
print("=" * 60)
print("CEO001 - Ahmed Banday (CEO)")
print(f"├── HM001 - {hm_emp.first_name} {hm_emp.last_name} (HR Manager)")
for eid in ['EMP002', 'EMP010']:
    if eid in employees:
        e = employees[eid]
        print(f"│   ├── {eid} - {e.first_name} {e.last_name} ({e.designation})")
for mid in ['MGR001', 'MGR002', 'MGR003', 'MGR004']:
    m = managers[mid]
    print(f"├── {mid} - {m.first_name} {m.last_name} ({m.designation})")
    subs = [eid for eid, ed in employees_data if ed[7] == mid]
    for i, eid in enumerate(subs):
        e = employees[eid]
        prefix = "│   └──" if i == len(subs) - 1 else "│   ├──"
        print(f"{prefix} {eid} - {e.first_name} {e.last_name} ({e.designation})")
print("=" * 60)
print(f"\nHR Login: admin / admin123")
print(f"CEO Login: CEO001 / ceo123")
print(f"Manager Login: MGR001 / manager123")
print(f"Employee Login: EMP001 / employee123")
print(f"Total: {Employee.objects.count()} employees, {Department.objects.count()} departments")
