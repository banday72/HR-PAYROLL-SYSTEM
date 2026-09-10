from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Leave, LeaveType
from .forms import LeaveForm, LeaveTypeForm, LeaveApprovalForm
from employees.views import get_employee
from employees.decorators import hr_required


@login_required
def leave_list(request):
    employee = get_employee(request.user)
    if employee:
        leaves = Leave.objects.filter(employee=employee)
    else:
        leaves = Leave.objects.all()

    status_filter = request.GET.get('status', '')
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    paginator = Paginator(leaves, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leaves/leave_list.html', {
        'leaves': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'is_employee': employee is not None,
    })


@login_required
def leave_create(request):
    employee = get_employee(request.user)
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            if employee:
                leave.employee = employee
            leave.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('leave_list')
    else:
        form = LeaveForm()
        if employee:
            form.fields['employee'].initial = employee
            form.fields['employee'].widget = forms.HiddenInput()
    return render(request, 'leaves/leave_form.html', {'form': form, 'title': 'Apply for Leave'})


@login_required
@hr_required
def leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        form = LeaveApprovalForm(request.POST)
        if form.is_valid():
            leave.status = form.cleaned_data['status']
            leave.approved_by = form.cleaned_data['approved_by']
            leave.save()
            messages.success(request, f'Leave request {leave.status}.')
            return redirect('leave_list')
    else:
        form = LeaveApprovalForm()
    return render(request, 'leaves/leave_approve.html', {'form': form, 'leave': leave})


@login_required
@hr_required
def leave_delete(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Leave deleted successfully.')
        return redirect('leave_list')
    return render(request, 'leaves/leave_confirm_delete.html', {'leave': leave})


@login_required
def leave_type_list(request):
    leave_types = LeaveType.objects.all()
    return render(request, 'leaves/leave_type_list.html', {'leave_types': leave_types})


@login_required
@hr_required
def leave_type_create(request):
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave type created successfully.')
            return redirect('leave_type_list')
    else:
        form = LeaveTypeForm()
    return render(request, 'leaves/leave_type_form.html', {'form': form, 'title': 'Add Leave Type'})


from django import forms as django_forms
