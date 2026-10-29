# 🎓 College Management Portal (Academic PBL)

A comprehensive, role-based College Management Portal built with **Django** and **MongoDB (PyMongo)**, featuring complete academic workflows for Administrators, Faculty, and Students.

---

## 🌟 Key Features

- **Multi-Role Authentication & Access Control**:
  - **Administrator**: Manage departments, courses, faculty, students, and publish institutional announcements.
  - **Faculty**: Record and monitor student attendance, manage examination marks/grades, view assigned courses.
  - **Student**: Access personalized dashboard, real-time subject-wise attendance percentage, examination results, and college notices.
- **Hybrid Database Architecture**:
  - **MongoDB (PyMongo)**: Stores all domain entities (Users, Students, Faculty, Departments, Courses, Attendance, Marks, Announcements) with unique constraints and indexing.
  - **SQLite**: Used strictly for Django's built-in session engine and CSRF protection.
- **Academic Analytics**:
  - Real-time calculation of student attendance percentages with low-attendance warnings (<75%).
  - Grade and percentage evaluations for examinations.
- **Automated Test Suite**:
  - Full suite of automated integration and unit tests covering authentication, database connectivity, authorization, data validation, and academic workflows.

---

## 🏗️ Technology Stack

- **Backend**: Python 3, Django (6.x)
- **Database**: MongoDB (via PyMongo 4.x), SQLite (session storage)
- **Frontend**: Bootstrap 5, HTML5, CSS3, FontAwesome icons
- **Environment Management**: python-dotenv

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ installed
- MongoDB Community Server installed and running on `localhost:27017`
- Git

### 2. Clone the Repository
```bash
git clone <repository-url>
cd ITL
```

### 3. Create & Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your MongoDB configuration in `.env` matches your environment:
```env
SECRET_KEY=college-portal-secure-academic-secret-key-2026-pbl-demo
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=college_management_portal
```

### 6. Apply Migrations & Seed MongoDB
```bash
# Apply Django session migrations
python manage.py migrate

# Initialize MongoDB indexes and populate demo data
python init_db.py
```

### 7. Run the Application
```bash
python manage.py runserver
```
Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your web browser.

---

## 🔑 Demo Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@123` |
| **Faculty** | `fac001` or `fac002` | `Faculty@123` |
| **Student** | `stu001` (to `stu005`) | `Student@123` |

---

## 🧪 Running Tests
To run the automated test suite:
```bash
python manage.py test tests
```
