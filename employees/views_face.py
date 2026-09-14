import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from employees.models import Employee


@login_required
def face_register(request):
    employee = None
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        pass
    if request.user.is_superuser and not employee:
        return render(request, 'face/face_register.html', {'employee': None, 'is_superuser': True})
    return render(request, 'face/face_register.html', {'employee': employee, 'is_superuser': False})


@csrf_exempt
def face_save(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            face_descriptors = data.get('descriptors', [])
            employee = Employee.objects.get(user=request.user)
            employee.face_data = json.dumps(face_descriptors)
            employee.face_registered = True
            employee.save()
            return JsonResponse({'status': 'ok', 'message': 'Face registered successfully'})
        except Employee.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No employee profile linked to your account'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)


@login_required
def face_verify_page(request):
    return render(request, 'face/face_verify.html')


@csrf_exempt
def face_verify(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            face_descriptors = data.get('descriptors', [])
            employee = Employee.objects.get(user=request.user)

            if not employee.face_registered or not employee.face_data:
                return JsonResponse({'status': 'error', 'message': 'No face registered'})

            stored = json.loads(employee.face_data)
            if not stored:
                return JsonResponse({'status': 'error', 'message': 'No face data stored'})

            for stored_desc in stored:
                for input_desc in face_descriptors:
                    if len(stored_desc) == len(input_desc):
                        distance = sum((a - b) ** 2 for a, b in zip(stored_desc, input_desc)) ** 0.5
                        if distance < 0.4:
                            return JsonResponse({'status': 'ok', 'message': 'Face verified'})

            return JsonResponse({'status': 'error', 'message': 'Face does not match'})
        except Employee.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No employee profile'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
