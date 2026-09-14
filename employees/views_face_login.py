import json
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from employees.models import Employee


def face_login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'face/face_login.html')


@csrf_exempt
def face_login_check(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            face_descriptors = data.get('descriptors', [])

            employees = Employee.objects.filter(
                face_registered=True,
                face_data__isnull=False,
                status='active',
                user__isnull=False,
            ).exclude(face_data='').select_related('user')

            best_match = None
            best_distance = 1.0

            for emp in employees:
                try:
                    stored = json.loads(emp.face_data)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not stored:
                    continue

                for stored_desc in stored:
                    for input_desc in face_descriptors:
                        if len(stored_desc) == len(input_desc):
                            distance = sum((a - b) ** 2 for a, b in zip(stored_desc, input_desc)) ** 0.5
                            if distance < 0.4 and distance < best_distance:
                                best_distance = distance
                                best_match = emp

            if best_match and best_match.user:
                login(request, best_match.user, backend='hr_payroll.backends.AuthorizedUserBackend')
                return JsonResponse({
                    'status': 'ok',
                    'message': f'Welcome {best_match.full_name}',
                    'employee_id': best_match.employee_id,
                    'redirect': '/'
                })

            return JsonResponse({'status': 'error', 'message': 'No matching face found. Try again or use password login.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
