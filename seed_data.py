import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from employees.models import Department, Employee
from attendance.models import Attendance
from leaves.models import LeaveType, Leave
from payroll.models import Payroll, PayrollPolicy
from datetime import date, time, timedelta
import calendar

print("Seeding database...")

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@hrpayroll.com', 'admin123')
    print("Created superuser: admin / admin123")

# Create payroll policy
policy, _ = PayrollPolicy.objects.get_or_create(
    name='Standard Company Policy',
    defaults={
        'working_days_per_month': 30,
        'absent_deduction_per_day': 0,
        'use_per_day_salary_for_absent': True,
        'half_day_deduction_percent': 50,
        'late_allowed_per_month': 3,
        'late_deduction_amount': 500,
        'approved_leave_paid': True,
        'tax_rate_percent': 10,
        'performance_bonus_enabled': True,
        'bonus_100_percent': 10,
        'bonus_95_percent': 5,
        'bonus_90_percent': 2,
        'bonus_below_90_percent': 0,
        'medical_allowance': 5000,
        'transport_allowance': 3000,
        'house_allowance_percent': 20,
        'is_active': True,
    }
)
print("Created payroll policy")

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

# Create employees with user accounts
employees_data = [
    ('EMP001', 'Ahmed', 'Khan', 'ahmed.khan@company.com', 'M', 'Engineering', 'Senior Developer', 85000),
    ('EMP002', 'Fatima', 'Ali', 'fatima.ali@company.com', 'F', 'Human Resources', 'HR Manager', 75000),
    ('EMP003', 'Omar', 'Raza', 'omar.raza@company.com', 'M', 'Finance', 'Financial Analyst', 70000),
    ('EMP004', 'Sara', 'Malik', 'sara.malik@company.com', 'F', 'Marketing', 'Marketing Lead', 72000),
    ('EMP005', 'Hassan', 'Iqbal', 'hassan.iqbal@company.com', 'M', 'Engineering', 'Full Stack Developer', 80000),
    ('EMP006', 'Ayesha', 'Noor', 'ayesha.noor@company.com', 'F', 'Operations', 'Operations Manager', 68000),
    ('EMP007', 'Bilal', 'Sheikh', 'bilal.sheikh@company.com', 'M', 'Sales', 'Sales Executive', 65000),
    ('EMP008', 'Zainab', 'Ahmed', 'zainab.ahmed@company.com', 'F', 'Engineering', 'DevOps Engineer', 82000),
    ('EMP009', 'Usman', 'Tariq', 'usman.tariq@company.com', 'M', 'Finance', 'Accountant', 62000),
    ('EMP010', 'Hira', 'Shah', 'hira.shah@company.com', 'F', 'Marketing', 'Content Specialist', 58000),
]

employees = {}
for emp_id, first, last, email, gender, dept_name, designation, salary in employees_data:
    emp, created = Employee.objects.get_or_create(
        employee_id=emp_id,
        defaults={
            'first_name': first,
            'last_name': last,
            'email': email,
            'gender': gender,
            'department': departments[dept_name],
            'designation': designation,
            'date_of_joining': date(2023, 1, 15),
            'salary': salary,
            'status': 'active',
        }
    )
    # Create user account for employee
    if not emp.user:
        user, user_created = User.objects.get_or_create(
            username=emp_id,
            defaults={
                'email': email,
                'first_name': first,
                'last_name': last,
                'is_staff': False,
            }
        )
        if user_created:
            user.set_password('employee123')
            user.save()
        emp.user = user
        emp.save()
    employees[emp_id] = emp
print(f"Created {len(employees)} employees with user accounts")

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

# Create attendance records for September 2026 (realistic patterns)
today = date(2026, 9, 8)

# Different attendance patterns per employee
patterns = {
    'EMP001': ['present'] * 5 + ['late'] * 1 + ['present'],  # Excellent: ~100%
    'EMP002': ['present'] * 4 + ['half_day'] * 1 + ['present'] * 2,  # Good: ~95%
    'EMP003': ['present'] * 3 + ['absent'] * 1 + ['present'] * 2 + ['late'],  # Average: ~85%
    'EMP004': ['present'] * 5 + ['holiday'] + ['present'],  # Excellent
    'EMP005': ['present'] * 6 + ['half_day'],  # Good
    'EMP006': ['present'] * 4 + ['late'] * 2 + ['present'],  # OK
    'EMP007': ['present'] * 3 + ['absent'] * 2 + ['present'] * 2,  # Poor: ~70%
    'EMP008': ['present'] * 5 + ['present'] * 2,  # Excellent
    'EMP009': ['present'] * 4 + ['half_day'] + ['late'] + ['present'],  # Good
    'EMP010': ['present'] * 2 + ['absent'] * 1 + ['present'] * 2 + ['half_day'] + ['present'],  # Average
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
            employee=emp,
            date=att_date,
            defaults={
                'clock_in': clock_in_time,
                'clock_out': clock_out_time,
                'status': status,
            }
        )
print("Created attendance records")

# Create leave requests
Leave.objects.get_or_create(
    employee=employees['EMP001'],
    leave_type=leave_types['Annual Leave'],
    start_date=date(2026, 9, 15),
    end_date=date(2026, 9, 20),
    defaults={'reason': 'Family vacation', 'status': 'approved', 'approved_by': 'Admin'}
)
Leave.objects.get_or_create(
    employee=employees['EMP003'],
    leave_type=leave_types['Sick Leave'],
    start_date=date(2026, 9, 10),
    end_date=date(2026, 9, 11),
    defaults={'reason': 'Medical appointment', 'status': 'pending'}
)
Leave.objects.get_or_create(
    employee=employees['EMP007'],
    leave_type=leave_types['Personal Leave'],
    start_date=date(2026, 9, 12),
    end_date=date(2026, 9, 12),
    defaults={'reason': 'Personal work', 'status': 'approved', 'approved_by': 'Admin'}
)
print("Created leave requests")

# Create sample payroll records (August 2026)
for emp_id, emp in employees.items():
    basic = emp.salary / 12
    allowances = basic * 0.15
    deductions = basic * 0.05
    tax = basic * 0.10
    net = basic + allowances - deductions - tax

    Payroll.objects.get_or_create(
        employee=emp,
        month=8,
        year=2026,
        defaults={
            'basic_salary': round(basic, 2),
            'allowances': round(allowances, 2),
            'deductions': round(deductions, 2),
            'tax': round(tax, 2),
            'net_salary': round(net, 2),
            'status': 'paid',
            'payment_date': date(2026, 8, 28),
            'generated_type': 'auto',
            'notes': 'Auto-generated from attendance data',
        }
    )

print("Created payroll records")

print("\n" + "=" * 50)
print("SEEDING COMPLETE!")
print("=" * 50)
print(f"HR Login: admin / admin123")
print(f"Employee Login: EMP001 / employee123")
print(f"               EMP002 / employee123")
print(f"               (use employee_id as username)")
print(f"Total: {Employee.objects.count()} employees, {Department.objects.count()} departments")
print(f"Attendance: {Attendance.objects.count()} records")
print(f"Payroll: {Payroll.objects.count()} records")
print(f"Policy: {PayrollPolicy.objects.count()} policies")
print("=" * 50)
