#!/bin/bash
# ============================================================
# PM Internship Scheme Portal - Setup Script
# ============================================================

echo "=================================================="
echo "  PM Internship Scheme Portal - Setup"
echo "=================================================="

# Step 1: Install Django
echo ""
echo "[1/4] Installing Django..."
pip install django>=4.2

# Step 2: Run migrations
echo ""
echo "[2/4] Running database migrations..."
python manage.py makemigrations student_portal
python manage.py makemigrations
python manage.py migrate

# Step 3: Create admin account
echo ""
echo "[3/4] Creating admin account..."
python manage.py setup_admin

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "=================================================="
echo "  PORTAL CREDENTIALS"
echo "=================================================="
echo ""
echo "  ADMIN PORTAL:"
echo "    URL      : http://127.0.0.1:8000/admin-portal/login/"
echo "    Username : admin"
echo "    Password : admin"
echo ""
echo "  STUDENT PORTAL:"
echo "    URL      : http://127.0.0.1:8000/student/"
echo "    Register yourself at /student/register/"
echo ""
echo "  MENTOR PORTAL:"
echo "    URL      : http://127.0.0.1:8000/mentor/login/"
echo "    (Add mentors via Admin Portal)"
echo ""
echo "=================================================="
echo ""
echo "Starting development server..."
echo "Open: http://127.0.0.1:8000"
echo ""
python manage.py runserver
