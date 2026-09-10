from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Department, Employee
from .forms import DepartmentForm, EmployeeForm


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

    if employee:
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
        }
    return render(request, 'dashboard.html', context)


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    search = request.GET.get('search', '')
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    paginator = Paginator(employees, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/employee_list.html', {
        'employees': page_obj,
        'page_obj': page_obj,
        'search': search,
    })


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/employee_detail.html', {'employee': employee})


@login_required
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
            messages.success(request, f'Employee created. Login: {emp.employee_id} / employee123')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
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
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'employees/department_list.html', {'departments': departments})


@login_required
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
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('department_list')
    return render(request, 'employees/department_confirm_delete.html', {'department': department})
