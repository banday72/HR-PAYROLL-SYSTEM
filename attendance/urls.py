from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('clock-in/', views.attendance_clock_in, name='attendance_clock_in'),
    path('clock-out/', views.attendance_clock_out, name='attendance_clock_out'),
    path('create/', views.attendance_create, name='attendance_create'),
    path('<int:pk>/edit/', views.attendance_update, name='attendance_update'),
    path('<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
]
