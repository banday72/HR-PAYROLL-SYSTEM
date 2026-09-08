from django.urls import path
from . import views

urlpatterns = [
    path('', views.leave_list, name='leave_list'),
    path('create/', views.leave_create, name='leave_create'),
    path('<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('<int:pk>/delete/', views.leave_delete, name='leave_delete'),
    path('types/', views.leave_type_list, name='leave_type_list'),
    path('types/create/', views.leave_type_create, name='leave_type_create'),
]
