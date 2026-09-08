# HR Payroll System

A complete HR Payroll System built with Django.

## Features
- Employee management (add, edit, delete)
- Attendance tracking (clock in/out)
- Leave management (apply, approve/reject)
- Auto payroll generation from attendance + leave data
- Salary slips (PDF export)
- Payroll policies (configurable deductions, bonuses, tax)

## Deployment to Vercel

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/hr-payroll-system.git
git push -u origin main
```

### Step 2: Deploy on Vercel
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "New Project"
4. Import your GitHub repository
5. Click "Deploy"

### Step 3: Set Environment Variables (Optional)
- `DEBUG` = `True` (for development)
- `SECRET_KEY` = your secret key

### Step 4: Access Your Site
- Your site will be at: `https://your-project.vercel.app`
- Login: `admin` / `admin123`
- Employee login: `EMP001` / `employee123`

## Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed sample data
python manage.py seed_data

# Run server
python manage.py runserver
```

## Project Structure
```
hr-payroll-system/
├── hr_payroll/          # Main settings
├── employees/           # Employee module
├── attendance/          # Attendance module
├── leaves/              # Leave module
├── payroll/             # Payroll module
├── templates/           # HTML templates
├── vercel_app/          # Vercel deployment
├── vercel.json          # Vercel config
├── requirements.txt     # Python dependencies
└── runtime.txt          # Python version
```
