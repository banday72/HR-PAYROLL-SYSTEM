from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Employee(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('terminated', 'Terminated')]
    ROLE_CHOICES = [('employee', 'Employee'), ('hr', 'HR'), ('manager', 'Manager')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.CharField(max_length=100, blank=True)
    date_of_joining = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    city = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    is_authorized = models.BooleanField(default=False, help_text='Only authorized users can login')
    must_change_password = models.BooleanField(default=False, help_text='Force password change on next login')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_hr(self):
        return self.role in ('hr', 'manager')

    @property
    def is_manager(self):
        return self.role == 'manager'

    class Meta:
        ordering = ['employee_id']


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('authorize', 'Authorize'),
        ('deauthorize', 'Deauthorize'),
        ('password_change', 'Password Change'),
        ('export', 'Export'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Audit Logs'
