from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0004_boutiqueproduct_budgetloan_boutiqueissue_payrollbreakdown'),
        ('employees', '0009_employee_reports_to'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicPayrollLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(default=uuid.uuid4, max_length=64, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.OneToOneField(on_delete=models.CASCADE, related_name='public_link', to='employees.employee')),
            ],
        ),
    ]
