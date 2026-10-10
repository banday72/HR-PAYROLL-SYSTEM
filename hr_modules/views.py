from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta

from employees.decorators import permission_required
from employees.permissions import permissions_for_user


def has_any_permission(user, *perms):
    return user.is_superuser or bool(perms and permissions_for_user(user) & set(perms))


def create_notification(employee, title, message, notif_type='info', link=''):
    from .models import Notification
    return Notification.objects.create(
        employee=employee, title=title, message=message,
        notif_type=notif_type, link=link
    )


# ============ ORG CHART ============
@login_required
def org_chart(request):
    from employees.models import Employee
    ceo = Employee.objects.filter(employee_id='CEO001').first()
    officers = Employee.objects.filter(reports_to=ceo, status='active') if ceo else []
    org_data = []
    for officer in officers:
        subs = Employee.objects.filter(reports_to=officer, status='active')
        org_data.append({'officer': officer, 'employees': list(subs)})
    return render(request, 'hr_modules/org_chart.html', {
        'ceo': ceo, 'org_data': org_data
    })


# ============ NOTIFICATIONS ============
@login_required
def notification_list(request):
    from employees.models import Employee
    from .models import Notification
    emp = Employee.objects.filter(user=request.user).first()
    if emp:
        notifs = Notification.objects.filter(employee=emp)
    elif request.user.is_superuser:
        notifs = Notification.objects.all()[:100]
    else:
        notifs = Notification.objects.none()
    return render(request, 'hr_modules/notification_list.html', {
        'notifications': notifs, 'unread_count': notifs.filter(is_read=False).count()
    })


@login_required
def notification_mark_read(request, pk):
    from .models import Notification
    notif = get_object_or_404(Notification, pk=pk)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    from employees.models import Employee
    from .models import Notification
    emp = Employee.objects.filter(user=request.user).first()
    if emp:
        Notification.objects.filter(employee=emp, is_read=False).update(is_read=True)
    return redirect('notification_list')


# ============ EMPLOYEE DOCUMENTS ============
@login_required
def document_list(request):
    from employees.models import Employee
    from .models import EmployeeDocument
    emp = Employee.objects.filter(user=request.user).first()
    if has_any_permission(request.user, 'manage_documents'):
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
    from employees.models import Employee
    from .models import EmployeeDocument
    emp = Employee.objects.filter(user=request.user).first()
    if request.method == 'POST':
        target_emp_id = request.POST.get('employee_id', emp.employee_id if emp else None)
        target_emp = Employee.objects.filter(employee_id=target_emp_id).first()
        if not target_emp:
            messages.error(request, 'Employee not found.')
            return redirect('document_list')
        if not (request.user.is_superuser or has_any_permission(request.user, 'manage_documents') or (emp and target_emp.pk == emp.pk)):
            messages.error(request, 'You can only upload documents for yourself.')
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
    from .models import EmployeeDocument
    doc = get_object_or_404(EmployeeDocument, pk=pk)
    file_bytes = base64.b64decode(doc.file_data)
    response = HttpResponse(file_bytes, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.file_name}"'
    return response


@login_required
def document_delete(request, pk):
    from .models import EmployeeDocument
    doc = get_object_or_404(EmployeeDocument, pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('document_list')
    return render(request, 'hr_modules/document_confirm_delete.html', {'doc': doc})


# ============ PERFORMANCE REVIEWS ============
@login_required
def review_list(request):
    from employees.models import Employee
    from .models import PerformanceReview
    from django.db.models import Avg
    emp = Employee.objects.filter(user=request.user).first()
    period_filter = request.GET.get('period', '')
    year_filter = request.GET.get('year', '')
    employee_filter = request.GET.get('employee', '')

    if has_any_permission(request.user, 'manage_reviews'):
        reviews = PerformanceReview.objects.all()
    elif emp:
        reviews = PerformanceReview.objects.filter(employee=emp)
    else:
        reviews = PerformanceReview.objects.none()

    if period_filter:
        reviews = reviews.filter(period=period_filter)
    if year_filter:
        reviews = reviews.filter(year=int(year_filter))
    if employee_filter:
        reviews = reviews.filter(employee__employee_id=employee_filter)

    avg_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
    total_reviews = reviews.count()
    completed = reviews.filter(status='completed').count()

    emp_stats = []
    if has_any_permission(request.user, 'manage_reviews'):
        all_emps = Employee.objects.filter(status='active')
        for e in all_emps:
            e_reviews = PerformanceReview.objects.filter(employee=e)
            e_avg = e_reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
            e_count = e_reviews.count()
            emp_stats.append({'employee': e, 'avg_rating': e_avg, 'review_count': e_count})

    return render(request, 'hr_modules/review_list.html', {
        'reviews': reviews, 'avg_rating': round(float(avg_rating), 2),
        'total_reviews': total_reviews, 'completed': completed,
        'emp_stats': emp_stats, 'period_filter': period_filter,
        'year_filter': year_filter, 'employee_filter': employee_filter,
    })


@login_required
@permission_required('manage_reviews')
def review_create(request):
    from employees.models import Employee
    from .models import PerformanceReview
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
    from .models import PerformanceReview
    review = get_object_or_404(PerformanceReview, pk=pk)
    return render(request, 'hr_modules/review_detail.html', {'review': review})


# ============ TRAINING MODULE ============
@login_required
def training_list(request):
    from .models import Training
    trainings = Training.objects.all()
    return render(request, 'hr_modules/training_list.html', {'trainings': trainings})


@login_required
@permission_required('manage_training')
def training_create(request):
    from employees.models import Employee
    from .models import Training
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
@permission_required('manage_training')
def training_enroll(request, pk):
    from employees.models import Employee
    from .models import Training, TrainingEnrollment
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
    from .models import Training, TrainingEnrollment
    training = get_object_or_404(Training, pk=pk)
    enrollments = TrainingEnrollment.objects.filter(training=training)
    return render(request, 'hr_modules/training_detail.html', {
        'training': training, 'enrollments': enrollments
    })


# ============ TRAVEL & REIMBURSEMENT ============
@login_required
def travel_list(request):
    from employees.models import Employee
    from .models import TravelRequest
    emp = Employee.objects.filter(user=request.user).first()
    if has_any_permission(request.user, 'view_all_travel'):
        travels = TravelRequest.objects.all()
    elif emp:
        travels = TravelRequest.objects.filter(employee=emp)
    else:
        travels = TravelRequest.objects.none()
    status_filter = request.GET.get('status', '')
    if status_filter:
        travels = travels.filter(status=status_filter)
    return render(request, 'hr_modules/travel_list.html', {'travels': travels, 'status_filter': status_filter})


@login_required
def travel_create(request):
    from employees.models import Employee
    from .models import TravelRequest
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
@permission_required('approve_travel')
def travel_action(request, pk):
    from .models import TravelRequest
    travel = get_object_or_404(TravelRequest, pk=pk)
    if request.method == 'POST':
        from employees.models import Employee
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
    from employees.models import Employee
    from .models import OvertimeRecord
    emp = Employee.objects.filter(user=request.user).first()
    if has_any_permission(request.user, 'view_all_overtime'):
        records = OvertimeRecord.objects.all()
    elif emp:
        records = OvertimeRecord.objects.filter(employee=emp)
    else:
        records = OvertimeRecord.objects.none()
    status_filter = request.GET.get('status', '')
    if status_filter:
        records = records.filter(status=status_filter)
    return render(request, 'hr_modules/overtime_list.html', {'records': records, 'status_filter': status_filter})


@login_required
def overtime_create(request):
    from employees.models import Employee
    from .models import OvertimeRecord
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
@permission_required('approve_overtime')
def overtime_action(request, pk):
    from .models import OvertimeRecord
    ot = get_object_or_404(OvertimeRecord, pk=pk)
    if request.method == 'POST':
        from employees.models import Employee
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
