# 🏛️ PM Internship Scheme Portal

A full-stack Django web application for the **PM Government Internship Scheme** with 3 separate Django apps — Student Portal, Mentor Portal, and Admin Portal.

---

## 📁 Project Structure

```
pm_internship_project/
├── pm_internship_project/          # Main Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── student_portal/                 # Django App 1 — Students
│   ├── models.py                   # CustomUser model with roles
│   ├── views.py
│   ├── urls.py
│   └── apps.py
├── mentor_portal/                  # Django App 2 — Mentors
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── apps.py
├── admin_portal/                   # Django App 3 — Admin
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── apps.py
│   └── management/
│       └── commands/
│           └── setup_admin.py      # Custom command to create admin
├── templates/
│   ├── base.html                   # Shared base template
│   ├── student_portal/
│   │   ├── home.html
│   │   ├── about.html
│   │   ├── register.html
│   │   ├── login.html
│   │   └── dashboard.html
│   ├── mentor_portal/
│   │   ├── login.html
│   │   └── dashboard.html
│   └── admin_portal/
│       ├── login.html
│       ├── dashboard.html
│       └── add_mentor.html
├── static/
├── db.sqlite3                      # Auto-generated SQLite database
├── manage.py
├── requirements.txt
└── setup_and_run.sh
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8+
- pip

### Quick Setup (Recommended)

```bash
# 1. Navigate to the project directory
cd pm_internship_project

# 2. Run the setup script (installs Django, runs migrations, creates admin)
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### Manual Setup

```bash
# 1. Install Django
pip install django>=4.2

# 2. Create and apply migrations
python manage.py makemigrations student_portal
python manage.py makemigrations
python manage.py migrate

# 3. Create admin account
python manage.py setup_admin

# 4. Run the server
python manage.py runserver
```

---

## 🔑 Portal Access

| Portal         | URL                                      | Credentials                    |
|----------------|------------------------------------------|--------------------------------|
| Student Portal | http://127.0.0.1:8000/student/           | Register yourself              |
| Mentor Portal  | http://127.0.0.1:8000/mentor/login/      | Added by Admin                 |
| Admin Portal   | http://127.0.0.1:8000/admin-portal/login/ | Username: `admin` / PW: `admin` |

---

## 🎯 Features

### Student Portal (`/student/`)
- **Home** — Government-style scheme banner, portal links
- **About** — Scheme objectives, benefits, eligibility
- **Register** — Self-registration with encrypted password
- **Login** — Email/password login (students only)
- **Dashboard** — Welcome message, profile, scheme info

### Mentor Portal (`/mentor/`)
- **Login** — Email/password (mentors added by admin only)
- **Dashboard** — Welcome message, profile details

### Admin Portal (`/admin-portal/`)
- **Login** — Username/password (admin only)
- **Dashboard** — Total students & mentors, view all lists
- **Add Mentor** — Create mentor accounts with role auto-set

---

## 🔐 Role-Based Access Control

| Role    | Dashboard         | Notes                                    |
|---------|-------------------|------------------------------------------|
| Student | Student Dashboard | Can self-register via portal             |
| Mentor  | Mentor Dashboard  | Only admin can create mentor accounts    |
| Admin   | Admin Dashboard   | Single admin via `setup_admin` command   |

All dashboards are protected with `@login_required`. Wrong-role access is blocked.

---

## 🎨 UI Theme

- **Framework**: Tailwind CSS (via CDN)
- **Colors**: Saffron (#FF9933), White, India Green (#138808), Navy Blue (#1a3a6b)
- **Design**: Indian Government portal style with tricolor accent stripes
- **Font**: System default — clean and professional

---

## 🗃️ Database

- **Engine**: SQLite (auto-created as `db.sqlite3`)
- **Custom User Model**: `student_portal.CustomUser` (extends `AbstractBaseUser`)
  - Fields: `email`, `full_name`, `role`, `is_active`, `is_staff`, `date_joined`
  - Roles: `student`, `mentor`, `admin`
  - Password: Encrypted using Django's `set_password()`

---

## 📡 URL Structure

```
/                           → Redirects to /student/
/student/                   → Home
/student/about/             → About
/student/register/          → Register
/student/login/             → Login
/student/dashboard/         → Dashboard (protected)
/student/logout/            → Logout

/mentor/login/              → Login
/mentor/dashboard/          → Dashboard (protected)
/mentor/logout/             → Logout

/admin-portal/login/        → Login
/admin-portal/dashboard/    → Dashboard (protected)
/admin-portal/add-mentor/   → Add Mentor (protected)
/admin-portal/logout/       → Logout
```
