from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Department, Employee
from .forms import DepartmentForm, EmployeeForm
from .decorators import hr_required


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
        context = {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'recent_employees': recent_employees,
            'pending_leaves': pending_leaves,
            'draft_payrolls': draft_payrolls,
            'is_employee': False,
            'is_hr': is_hr,
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
            emp = form.save()
            from django.contrib.auth.models import User
            user = User.objects.create_user(
                username=emp.employee_id,
                email=emp.email,
                password='employee123',
                first_name=emp.first_name,
                last_name=emp.last_name,
            )
            emp.user = user
            emp.save()
            messages.success(request, f'Employee created. Login: {emp.employee_id} / employee123. Go to Authorized Users to grant login access.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
@hr_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
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
        if employee.user:
            employee.user.delete()
        employee.delete()
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
            form.save()
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
        department.delete()
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
        employee.save()
        if employee.is_authorized:
            if new_password and employee.user:
                employee.user.set_password(new_password)
                employee.user.save()
                messages.success(request, f'{employee.full_name} authorized. Username: {employee.employee_id} | Password: {new_password}')
            else:
                messages.success(request, f'{employee.full_name} authorized. Username: {employee.employee_id} | Default password: employee123')
        else:
            messages.warning(request, f'{employee.full_name} has been deauthorized. They can no longer login.')
    return redirect('authorized_users')
