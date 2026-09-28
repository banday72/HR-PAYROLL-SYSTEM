from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from employees.models import Employee
from .models import (
    Notification, EmployeeDocument, PerformanceReview,
    Training, TrainingEnrollment, TravelRequest, OvertimeRecord
)


# ============ ORG CHART ============
@login_required
def org_chart(request):
    ceo = Employee.objects.filter(employee_id='CEO001').first()
    officers = Employee.objects.filter(reports_to=ceo, status='active') if ceo else []
    employees_map = {}
    for emp in Employee.objects.filter(status='active').select_related('reports_to'):
        if emp.reports_to_id:
            employees_map.setdefault(emp.reports_to_id, []).append(emp)
    return render(request, 'hr_modules/org_chart.html', {
        'ceo': ceo, 'officers': officers, 'employees_map': employees_map
    })


# ============ NOTIFICATIONS ============
@login_required
def notification_list(request):
    emp = Employee.objects.filter(user=request.user).first()
    if emp:
        notifs = Notification.objects.filter(employee=emp)
    elif request.user.is_superuser:
        notifs = Notification.objects.all()[:100]
    else:
        notifs = Notification.objects.none()
    unread = notifs.filter(is_read=False).count()
    return render(request, 'hr_modules/notification_list.html', {
        'notifications': notifs, 'unread_count': unread
    })


@login_required
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    emp = Employee.objects.filter(user=request.user).first()
    if emp:
        Notification.objects.filter(employee=emp, is_read=False).update(is_read=True)
    return redirect('notification_list')


def create_notification(employee, title, message, notif_type='info', link=''):
    return Notification.objects.create(
        employee=employee, title=title, message=message,
        notif_type=notif_type, link=link
    )


# ============ EMPLOYEE DOCUMENTS ============
@login_required
def document_list(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.user.is_superuser or (emp and emp.is_hr):
        docs = EmployeeDocument.objects.all()
        emp_filter = request.GET.get('employee')
        if emp_filter:
            docs = docs.filter(employee__employee_id=emp_filter)
    elif emp:
        docs = EmployeeDocument.objects.filter(employee=emp)
    else:
        docs = EmployeeDocument.objects.none()
    return render(request, 'hr_modules/document_list.html', {'documents': docs})


@login_required
def document_upload(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.method == 'POST':
        target_emp_id = request.POST.get('employee_id', emp.employee_id if emp else None)
        target_emp = Employee.objects.filter(employee_id=target_emp_id).first()
        if not target_emp:
            messages.error(request, 'Employee not found.')
            return redirect('document_list')

        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            import base64
            file_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
            doc_type = request.POST.get('doc_type', 'other')
            title = request.POST.get('title', uploaded_file.name)
            EmployeeDocument.objects.create(
                employee=target_emp, doc_type=doc_type, title=title,
                file_data=file_data, file_name=uploaded_file.name,
                file_size=uploaded_file.size, notes=request.POST.get('notes', '')
            )
            messages.success(request, f'Document "{title}" uploaded successfully.')
            return redirect('document_list')
        else:
            messages.error(request, 'Please select a file.')
    return render(request, 'hr_modules/document_upload.html', {
        'employees': Employee.objects.filter(status='active')
    })


@login_required
def document_download(request, pk):
    import base64
    from django.http import HttpResponse
    doc = get_object_or_404(EmployeeDocument, pk=pk)
    file_bytes = base64.b64decode(doc.file_data)
    response = HttpResponse(file_bytes, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.file_name}"'
    return response


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(EmployeeDocument, pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('document_list')
    return render(request, 'hr_modules/document_confirm_delete.html', {'doc': doc})


# ============ PERFORMANCE REVIEWS ============
@login_required
def review_list(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.user.is_superuser or (emp and emp.is_hr):
        reviews = PerformanceReview.objects.all()
    elif emp:
        reviews = PerformanceReview.objects.filter(employee=emp)
    else:
        reviews = PerformanceReview.objects.none()
    return render(request, 'hr_modules/review_list.html', {'reviews': reviews})


@login_required
def review_create(request):
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        emp = get_object_or_404(Employee, employee_id=emp_id)
        reviewer = Employee.objects.filter(user=request.user).first()
        review = PerformanceReview.objects.create(
            employee=emp, reviewer=reviewer,
            period=request.POST.get('period'),
            year=int(request.POST.get('year', date.today().year)),
            technical_score=int(request.POST.get('technical_score', 3)),
            communication_score=int(request.POST.get('communication_score', 3)),
            teamwork_score=int(request.POST.get('teamwork_score', 3)),
            leadership_score=int(request.POST.get('leadership_score', 3)),
            initiative_score=int(request.POST.get('initiative_score', 3)),
            strengths=request.POST.get('strengths', ''),
            improvements=request.POST.get('improvements', ''),
            goals=request.POST.get('goals', ''),
            comments=request.POST.get('comments', ''),
            status='completed'
        )
        create_notification(emp, 'Performance Review',
            f'Your {review.get_period_display()} {review.year} review is ready. Rating: {review.overall_rating}/5',
            'info', 'review_list')
        messages.success(request, f'Review created for {emp.first_name} {emp.last_name}.')
        return redirect('review_list')
    return render(request, 'hr_modules/review_form.html', {
        'employees': Employee.objects.filter(status='active')
    })


@login_required
def review_detail(request, pk):
    review = get_object_or_404(PerformanceReview, pk=pk)
    return render(request, 'hr_modules/review_detail.html', {'review': review})


# ============ TRAINING MODULE ============
@login_required
def training_list(request):
    trainings = Training.objects.all()
    return render(request, 'hr_modules/training_list.html', {'trainings': trainings})


@login_required
def training_create(request):
    if request.method == 'POST':
        creator = Employee.objects.filter(user=request.user).first()
        training = Training.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            provider=request.POST.get('provider', ''),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            status=request.POST.get('status', 'planned'),
            created_by=creator
        )
        messages.success(request, f'Training "{training.title}" created.')
        return redirect('training_list')
    return render(request, 'hr_modules/training_form.html')


@login_required
def training_enroll(request, pk):
    training = get_object_or_404(Training, pk=pk)
    if request.method == 'POST':
        emp_ids = request.POST.getlist('employees')
        count = 0
        for eid in emp_ids:
            emp = Employee.objects.filter(employee_id=eid).first()
            if emp:
                TrainingEnrollment.objects.get_or_create(training=training, employee=emp)
                create_notification(emp, 'Training Enrollment',
                    f'You have been enrolled in "{training.title}"', 'info', 'training_list')
                count += 1
        messages.success(request, f'{count} employees enrolled.')
        return redirect('training_list')
    return render(request, 'hr_modules/training_enroll.html', {
        'training': training,
        'employees': Employee.objects.filter(status='active')
    })


@login_required
def training_detail(request, pk):
    training = get_object_or_404(Training, pk=pk)
    enrollments = TrainingEnrollment.objects.filter(training=training)
    return render(request, 'hr_modules/training_detail.html', {
        'training': training, 'enrollments': enrollments
    })


# ============ TRAVEL & REIMBURSEMENT ============
@login_required
def travel_list(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.user.is_superuser or (emp and emp.is_hr):
        travels = TravelRequest.objects.all()
    elif emp:
        travels = TravelRequest.objects.filter(employee=emp)
    else:
        travels = TravelRequest.objects.none()
    return render(request, 'hr_modules/travel_list.html', {'travels': travels})


@login_required
def travel_create(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.method == 'POST':
        import base64
        receipt = request.FILES.get('receipt')
        receipt_data = base64.b64encode(receipt.read()).decode('utf-8') if receipt else ''
        travel = TravelRequest.objects.create(
            employee=emp,
            destination=request.POST.get('destination'),
            purpose=request.POST.get('purpose'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            estimated_cost=request.POST.get('estimated_cost', 0),
            receipt_data=receipt_data,
            notes=request.POST.get('notes', '')
        )
        if emp.reports_to:
            create_notification(emp.reports_to, 'Travel Request',
                f'{emp.first_name} {emp.last_name} requests travel to {travel.destination}',
                'warning', 'travel_list')
        messages.success(request, 'Travel request submitted.')
        return redirect('travel_list')
    return render(request, 'hr_modules/travel_form.html')


@login_required
def travel_action(request, pk):
    travel = get_object_or_404(TravelRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        reviewer = Employee.objects.filter(user=request.user).first()
        travel.status = action
        travel.approved_by = reviewer
        travel.save()
        create_notification(travel.employee, f'Travel {action.title()}',
            f'Your travel to {travel.destination} has been {action}.',
            'success' if action == 'approved' else 'danger', 'travel_list')
        messages.success(request, f'Travel request {action}.')
        return redirect('travel_list')
    return render(request, 'hr_modules/travel_action.html', {'travel': travel})


# ============ OVERTIME TRACKING ============
@login_required
def overtime_list(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.user.is_superuser or (emp and emp.is_hr):
        records = OvertimeRecord.objects.all()
    elif emp:
        records = OvertimeRecord.objects.filter(employee=emp)
    else:
        records = OvertimeRecord.objects.none()
    return render(request, 'hr_modules/overtime_list.html', {'records': records})


@login_required
def overtime_create(request):
    emp = Employee.objects.filter(user=request.user).first()
    if request.method == 'POST':
        ot = OvertimeRecord.objects.create(
            employee=emp,
            date=request.POST.get('date'),
            hours=request.POST.get('hours'),
            reason=request.POST.get('reason'),
            rate_multiplier=request.POST.get('rate_multiplier', 1.5)
        )
        if emp.reports_to:
            create_notification(emp.reports_to, 'Overtime Request',
                f'{emp.first_name} {emp.last_name} requests {ot.hours}h overtime on {ot.date}',
                'warning', 'overtime_list')
        messages.success(request, 'Overtime request submitted.')
        return redirect('overtime_list')
    return render(request, 'hr_modules/overtime_form.html')


@login_required
def overtime_action(request, pk):
    ot = get_object_or_404(OvertimeRecord, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        reviewer = Employee.objects.filter(user=request.user).first()
        ot.status = action
        ot.approved_by = reviewer
        ot.save()
        create_notification(ot.employee, f'Overtime {action.title()}',
            f'Your overtime on {ot.date} ({ot.hours}h) has been {action}.',
            'success' if action == 'approved' else 'danger', 'overtime_list')
        messages.success(request, f'Overtime {action}.')
        return redirect('overtime_list')
    return render(request, 'hr_modules/overtime_action.html', {'record': ot})
