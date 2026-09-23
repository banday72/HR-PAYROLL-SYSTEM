import csv
import io
import base64
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Department, Employee, AuditLog
from .forms import DepartmentForm, EmployeeForm, ProfileForm
from .decorators import hr_required
from .audit import log_audit


def generate_employee_id():
    last_emp = Employee.objects.order_by('-id').first()
    if last_emp and last_emp.employee_id.startswith('EMP'):
        try:
            last_num = int(last_emp.employee_id.replace('EMP', ''))
            return f'EMP{last_num + 1:03d}'
        except ValueError:
            pass
    count = Employee.objects.count()
    return f'EMP{count + 1:03d}'


def get_employee(user):
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return None


@login_required
def dashboard(request):
    employee = get_employee(request.user)
    from leaves.models import Leave
    from payroll.models import Payroll
    from attendance.models import Attendance
    from datetime import date

    if employee and employee.must_change_password:
        messages.warning(request, 'You must change your password before continuing.')
        return redirect('change_password')

    is_hr = False
    if employee and employee.is_hr:
        is_hr = True

    if employee and not is_hr:
        today = date.today()
        my_attendance = Attendance.objects.filter(employee=employee, date=today).first()
        my_leaves = Leave.objects.filter(employee=employee).count()
        my_pending_leaves = Leave.objects.filter(employee=employee, status='pending').count()
        my_payrolls = Payroll.objects.filter(employee=employee)[:5]
        context = {
            'employee': employee,
            'my_attendance': my_attendance,
            'my_leaves_count': my_leaves,
            'my_pending_leaves': my_pending_leaves,
            'my_payrolls': my_payrolls,
            'is_employee': True,
            'is_hr': False,
        }
    else:
        total_employees = Employee.objects.filter(status='active').count()
        total_departments = Department.objects.count()
        recent_employees = Employee.objects.all()[:5]
        pending_leaves = Leave.objects.filter(status='pending').count()
        draft_payrolls = Payroll.objects.filter(status='draft').count()
        today_birthdays = Employee.objects.filter(
            date_of_birth__month=date.today().month,
            date_of_birth__day=date.today().day,
            status='active'
        )
        context = {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'recent_employees': recent_employees,
            'pending_leaves': pending_leaves,
            'draft_payrolls': draft_payrolls,
            'is_employee': False,
            'is_hr': is_hr,
            'today_birthdays': today_birthdays,
        }
    return render(request, 'dashboard.html', context)


@login_required
@hr_required
def employee_list(request):
    employees = Employee.objects.select_related('department').all()
    search = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(designation__icontains=search) |
            Q(department__name__icontains=search) |
            Q(city__icontains=search)
        )
    if department_id:
        employees = employees.filter(department_id=department_id)
    if status:
        employees = employees.filter(status=status)
    paginator = Paginator(employees, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    departments = Department.objects.all()
    return render(request, 'employees/employee_list.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'search': search,
        'departments': departments,
        'selected_department': department_id,
        'selected_status': status,
    })


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    current_employee = get_employee(request.user)
    is_hr = current_employee.is_hr if current_employee else request.user.is_superuser
    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'is_hr': is_hr,
    })


@login_required
@hr_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.employee_id = generate_employee_id()
            emp.save()
            user = User.objects.create_user(
                username=emp.employee_id,
                email=emp.email,
                password='employee123',
                first_name=emp.first_name,
                last_name=emp.last_name,
            )
            emp.user = user
            emp.must_change_password = True
            emp.save()
            log_audit(user=request.user, action='create', model_name='Employee',
                      object_id=emp.employee_id, description=f'Created employee {emp.full_name}', request=request)
            messages.success(request, f'Employee created. Login: {emp.employee_id} / employee123. Go to Authorized Users to grant login access.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
        form.fields['employee_id_preview'].initial = generate_employee_id()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
@hr_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            log_audit(user=request.user, action='update', model_name='Employee',
                      object_id=employee.employee_id, description=f'Updated employee {employee.full_name}', request=request)
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_detail', pk=pk)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
@hr_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        name = employee.full_name
        emp_id = employee.employee_id
        if employee.user:
            employee.user.delete()
        employee.delete()
        log_audit(user=request.user, action='delete', model_name='Employee',
                  object_id=emp_id, description=f'Deleted employee {name}', request=request)
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employee_list')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})


@login_required
@hr_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'employees/department_list.html', {'departments': departments})


@login_required
@hr_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            log_audit(user=request.user, action='create', model_name='Department',
                      object_id=dept.name, description=f'Created department {dept.name}', request=request)
            messages.success(request, 'Department created successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'employees/department_form.html', {'form': form, 'title': 'Add Department'})


@login_required
@hr_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            log_audit(user=request.user, action='update', model_name='Department',
                      object_id=department.name, description=f'Updated department {department.name}', request=request)
            messages.success(request, 'Department updated successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'employees/department_form.html', {'form': form, 'title': 'Edit Department'})


@login_required
@hr_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = department.name
        department.delete()
        log_audit(user=request.user, action='delete', model_name='Department',
                  object_id=name, description=f'Deleted department {name}', request=request)
        messages.success(request, 'Department deleted successfully.')
        return redirect('department_list')
    return render(request, 'employees/department_confirm_delete.html', {'department': department})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            employee = get_employee(request.user)
            if employee and employee.must_change_password:
                employee.must_change_password = False
                employee.save()
            log_audit(user=request.user, action='password_change', model_name='User',
                      object_id=request.user.username, description='Password changed', request=request)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {'form': form})


@login_required
@hr_required
def authorized_users(request):
    employees = Employee.objects.select_related('user', 'department').all()
    search = request.GET.get('search', '')
    auth_filter = request.GET.get('auth_filter', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    if auth_filter == 'authorized':
        employees = employees.filter(is_authorized=True)
    elif auth_filter == 'unauthorized':
        employees = employees.filter(is_authorized=False)
    paginator = Paginator(employees, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/authorized_users.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'search': search,
        'auth_filter': auth_filter,
    })


@login_required
@hr_required
def toggle_authorize(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        employee.is_authorized = not employee.is_authorized
        if not employee.is_authorized:
            employee.approved_by_manager = False
            employee.approved_by = None
            employee.approved_at = None
        employee.save()
        if employee.is_authorized:
            action = 'authorize'
            if employee.role in ('hr', 'manager'):
                employee.approved_by_manager = True
                employee.approved_by = request.user
                from django.utils import timezone
                employee.approved_at = timezone.now()
                employee.save()
                if new_password and employee.user:
                    employee.user.set_password(new_password)
                    employee.user.save()
                    messages.success(request, f'{employee.full_name} (HR/Manager) authorized directly. Username: {employee.employee_id} | Password: {new_password}')
                else:
                    messages.success(request, f'{employee.full_name} (HR/Manager) authorized directly. Username: {employee.employee_id} | Default password: employee123')
            else:
                messages.info(request, f'{employee.full_name} authorized by you. Waiting for Manager approval before they can login.')
        else:
            action = 'deauthorize'
            messages.warning(request, f'{employee.full_name} has been deauthorized. They can no longer login.')
        log_audit(user=request.user, action=action, model_name='Employee',
                  object_id=employee.employee_id, description=f'{action.title()}d {employee.full_name}', request=request)
    return redirect('authorized_users')


@login_required
def pending_approvals(request):
    employee = get_employee(request.user)
    is_manager = request.user.is_superuser or (employee and employee.role == 'manager')
    if not is_manager:
        messages.error(request, 'Only Managers can access this page.')
        return redirect('dashboard')

    pending = Employee.objects.select_related('department', 'approved_by').filter(
        is_authorized=True, approved_by_manager=False, status='active', role='employee'
    )
    search = request.GET.get('search', '')
    if search:
        pending = pending.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    paginator = Paginator(pending, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/pending_approvals.html', {
        'pending_employees': page_obj,
        'page_obj': page_obj,
        'search': search,
    })


@login_required
def manager_approve(request, pk):
    employee_obj = get_employee(request.user)
    is_manager = request.user.is_superuser or (employee_obj and employee_obj.role == 'manager')
    if not is_manager:
        messages.error(request, 'Only Managers can approve authorizations.')
        return redirect('dashboard')

    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'approve':
            emp.approved_by_manager = True
            emp.approved_by = request.user
            from django.utils import timezone
            emp.approved_at = timezone.now()
            emp.save()
            new_password = request.POST.get('new_password', '').strip()
            if new_password and emp.user:
                emp.user.set_password(new_password)
                emp.user.save()
                messages.success(request, f'{emp.full_name} approved. They can now login. Username: {emp.employee_id} | Password: {new_password}')
            else:
                messages.success(request, f'{emp.full_name} approved. They can now login. Username: {emp.employee_id} | Default password: employee123')
            log_audit(user=request.user, action='authorize', model_name='Employee',
                      object_id=emp.employee_id, description=f'Manager approved {emp.full_name}', request=request)
        elif action == 'reject':
            emp.is_authorized = False
            emp.approved_by_manager = False
            emp.save()
            messages.warning(request, f'{emp.full_name} authorization rejected.')
            log_audit(user=request.user, action='deauthorize', model_name='Employee',
                      object_id=emp.employee_id, description=f'Manager rejected {emp.full_name}', request=request)
    return redirect('pending_approvals')


@login_required
@hr_required
def bulk_import_employees(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            created_count = 0
            skipped_count = 0
            errors = []

            for row in reader:
                try:
                    emp_id = row.get('employee_id', '').strip()
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    email = row.get('email', '').strip()
                    department_name = row.get('department', '').strip()
                    designation = row.get('designation', '').strip()
                    salary = row.get('salary', '0').strip()
                    role = row.get('role', 'employee').strip().lower()

                    if not first_name or not last_name or not email:
                        skipped_count += 1
                        continue

                    if not emp_id:
                        emp_id = generate_employee_id()
                    elif Employee.objects.filter(employee_id=emp_id).exists():
                        skipped_count += 1
                        continue

                    if Employee.objects.filter(email=email).exists():
                        skipped_count += 1
                        continue

                    department = None
                    if department_name:
                        department, _ = Department.objects.get_or_create(name=department_name)

                    emp = Employee.objects.create(
                        employee_id=emp_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        department=department,
                        designation=designation,
                        salary=float(salary),
                        role=role if role in ('employee', 'hr', 'manager') else 'employee',
                        date_of_joining=date.today(),
                        status='active',
                    )

                    user = User.objects.create_user(
                        username=emp_id,
                        email=email,
                        password='employee123',
                        first_name=first_name,
                        last_name=last_name,
                    )
                    emp.user = user
                    emp.must_change_password = True
                    emp.save()
                    created_count += 1

                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Row error: {str(e)}")

            log_audit(user=request.user, action='create', model_name='Employee',
                      description=f'Bulk import: {created_count} created, {skipped_count} skipped', request=request)

            if created_count > 0:
                messages.success(request, f'Successfully imported {created_count} employees. {skipped_count} skipped.')
            else:
                messages.warning(request, f'No employees imported. {skipped_count} rows skipped.')

            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)

            return redirect('employee_list')

        except Exception as e:
            messages.error(request, f'Error reading CSV file: {str(e)}')
            return redirect('employee_list')

    return render(request, 'employees/bulk_import.html')


@login_required
@hr_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('user').all()
    search = request.GET.get('search', '')
    action_filter = request.GET.get('action', '')
    if search:
        logs = logs.filter(
            Q(description__icontains=search) |
            Q(object_id__icontains=search) |
            Q(user__username__icontains=search)
        )
    if action_filter:
        logs = logs.filter(action=action_filter)
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/audit_log.html', {
        'logs': page_obj,
        'page_obj': page_obj,
        'search': search,
        'action_filter': action_filter,
    })


@login_required
def profile_update(request):
    user = request.user
    employee = get_employee(user)
    if not employee and user.is_superuser:
        try:
            employee, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': f'ADMIN{user.id}',
                    'first_name': user.first_name or user.username,
                    'last_name': user.last_name or '',
                    'email': user.email or f'admin{user.id}@admin.local',
                    'date_of_joining': date.today(),
                    'salary': 0,
                    'role': 'manager',
                    'status': 'active',
                    'designation': 'Administrator',
                }
            )
        except Exception:
            employee = None
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            if employee:
                try:
                    if 'profile_picture' in request.FILES:
                        f = request.FILES['profile_picture']
                        ext = f.name.rsplit('.', 1)[-1].lower()
                        mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'pdf': 'application/pdf'}
                        mime = mime_map.get(ext, 'application/octet-stream')
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                        employee.profile_picture_b64 = f'data:{mime};base64,{b64}'
                    if request.POST.get('designation'):
                        employee.designation = request.POST['designation']
                    employee.save()
                except Exception as e:
                    messages.warning(request, f'Profile saved but file upload failed: {str(e)}')
                    return redirect('profile_update')
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_update')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'employees/profile_update.html', {
        'form': form,
        'employee': employee,
    })
