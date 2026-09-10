import os, sys, django, random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from employees.models import Department, Employee

random.seed(42)

cities = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan', 'Peshawar', 'Quetta', 'Sialkot', 'Gujranwala']
departments_list = ['Information Technology', 'Finance', 'Human Resources', 'Marketing', 'Sales', 'Operations', 'Administration', 'Customer Support', 'Information Security', 'Artificial Intelligence']
designations = {
    'Information Technology': ['Software Engineer', 'DevOps Engineer', 'QA Engineer', 'System Administrator', 'IT Intern'],
    'Finance': ['Accountant', 'Financial Analyst', 'Finance Officer'],
    'Human Resources': ['HR Manager', 'HR Executive', 'HR Assistant'],
    'Marketing': ['Marketing Executive', 'Digital Marketing Specialist'],
    'Sales': ['Sales Manager', 'Sales Executive', 'Sales Representative', 'Business Development Officer'],
    'Operations': ['Operations Manager', 'Operations Executive', 'Operations Coordinator'],
    'Administration': ['Admin Manager', 'Admin Officer'],
    'Customer Support': ['Support Agent', 'Support Team Lead'],
    'Information Security': ['Security Analyst', 'VAPT Analyst', 'Security Engineer'],
    'Artificial Intelligence': ['AI Engineer', 'ML Analyst', 'ML Engineer', 'AI Intern'],
}

status_choices = ['active'] * 6 + ['inactive'] * 2 + ['terminated'] * 2
performance_choices = [1, 2, 3, 4, 5]
performance_weights = [5, 10, 40, 30, 15]

last_names = ['Ahmed', 'Khan', 'Ali', 'Malik', 'Hussain', 'Butt', 'Chaudhry', 'Raza', 'Shah', 'Sheikh',
              'Nawaz', 'Qureshi', 'Siddiqui', 'Farooq', 'Iqbal', 'Javed', 'Rashid', 'Akhtar', 'Bashir', 'Chishti',
              'Durrani', 'Gilani', 'Hashmi', 'Jilani', 'Kazmi', 'Memon', 'Niazi', 'Osman', 'Qazi', 'Rizvi',
              'Saeed', 'Tariq', 'Usmani', 'Yousuf', 'Zaidi', 'Ansari', 'Bhatti', 'Cheema', 'Dar', 'Gondal',
              'Hayat', 'Ibrahim', 'Javaid', 'Lodhi', 'Mughal', 'Naqvi', 'Pasha', 'Rai', 'Sarwar', 'Turk']

first_names_m = ['Muhammad', 'Ali', 'Hassan', 'Hussein', 'Ahmed', 'Usman', 'Umar', 'Bilal', 'Hamza', 'Kamran',
                 'Faisal', 'Asif', 'Imran', 'Nadeem', 'Tariq', 'Javed', 'Rashid', 'Irfan', 'Salman', 'Faizan',
                 'Zain', 'Omar', 'Saad', 'Danish', 'Waleed', 'Arslan', 'Taimoor', 'Shehryar', 'Moiz', 'Ayan']

first_names_f = ['Fatima', 'Ayesha', 'Zainab', 'Maryam', 'Hira', 'Sana', 'Nida', 'Mehwish', 'Anum', 'Sobia',
                 'Asma', 'Nadia', 'Samina', 'Nazia', 'Rubab', 'Maham', 'Maira', 'Iqra', 'Saima', 'Bushra']

salaries_by_dept = {
    'Information Technology': (70000, 345000),
    'Finance': (60000, 335000),
    'Human Resources': (65000, 335000),
    'Marketing': (100000, 345000),
    'Sales': (100000, 345000),
    'Operations': (60000, 325000),
    'Administration': (70000, 345000),
    'Customer Support': (60000, 295000),
    'Information Security': (100000, 345000),
    'Artificial Intelligence': (60000, 275000),
}

existing_count = Employee.objects.count()
print(f"Existing employees: {existing_count}")

# Create departments first
for d in departments_list:
    Department.objects.get_or_create(name=d, defaults={'description': f'{d} department'})

needed = 1000 - existing_count
print(f"Need to create: {needed} more employees")

created = 0
used_emails = set()

for i in range(needed):
    while True:
        emp_num = existing_count + i + 1
        emp_id = f"EMP{emp_num:04d}"
        if not Employee.objects.filter(employee_id=emp_id).exists():
            break
        emp_num += 1
        emp_id = f"EMP{emp_num:04d}"

    gender = random.choice(['M', 'F'])
    if gender == 'M':
        first_name = random.choice(first_names_m)
    else:
        first_name = random.choice(first_names_f)
    last_name = random.choice(last_names)

    dept_name = random.choice(departments_list)
    designation = random.choice(designations[dept_name])
    city = random.choice(cities)

    sal_min, sal_max = salaries_by_dept[dept_name]
    salary = random.randint(sal_min // 1000, sal_max // 1000) * 1000

    dob = datetime(1970, 1, 1) + timedelta(days=random.randint(0, 10000))
    doj = datetime(2010, 1, 1) + timedelta(days=random.randint(0, 5000))

    base_email = f"{first_name.lower()}.{last_name.lower()}{emp_num}@demo-company.com"
    email = base_email

    status = random.choice(status_choices)
    perf = random.choices(performance_choices, weights=performance_weights)[0]

    try:
        Employee.objects.create(
            employee_id=emp_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=Department.objects.get(name=dept_name),
            designation=designation,
            date_of_joining=doj.date(),
            salary=salary,
            city=city,
            status=status,
            date_of_birth=dob.date(),
        )
        created += 1
    except Exception as e:
        print(f"Error creating {emp_id}: {e}")

print(f"Created: {created}")
print(f"Total employees: {Employee.objects.count()}")
print("DONE!")
