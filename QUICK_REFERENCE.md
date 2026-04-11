# 🎯 Students System - Quick Reference

## 📍 Key URLs

| Purpose | URL |
|---------|-----|
| Admin Dashboard | `http://localhost:5173/dashboard` |
| Public Form | `http://localhost:5173/student-form` |
| API Docs | `http://localhost:8000/docs` |
| Health Check | `http://localhost:8000/health` |

## 👤 Test Account for Admin

```
Email: admin@example.com
Password: admin123
```

## 📚 Main Files Created/Modified

### Backend
```
backend/app/models/student.py          ✅ NEW - Student model
backend/app/api/v1/students.py         ✅ NEW - API endpoints
backend/main.py                         ✏️ MODIFIED - Added students router
backend/app/core/seed.py                ✏️ MODIFIED - Added Students widget
```

### Frontend
```
src/components/widgets/AdminStudentsWidget.jsx    ✅ NEW - Admin widget
src/pages/ShareStudentForm.jsx                    ✅ NEW - Public form
src/App.jsx                                       ✏️ MODIFIED - Added route
src/components/DashboardGrid.jsx                  ✏️ MODIFIED - Added widget mapping
src/styles/widgets.css                            ✏️ MODIFIED - Added styles
```

## 🔑 Key Permissions

```
students:read    - View student records
students:write   - Create and edit students
students:delete  - Delete students
```

## 🛠️ API Endpoints

### Admin (Requires Authentication)
```
GET    /api/v1/students/              - List all students
GET    /api/v1/students/{id}          - Get one student
POST   /api/v1/students/              - Create student
PATCH  /api/v1/students/{id}          - Update student
DELETE /api/v1/students/{id}          - Delete student
```

### Public (No Auth Required)
```
POST   /api/v1/students/public/submit-form         - Submit form
GET    /api/v1/students/public/form-status/{code}  - Check status
```

## 📊 Database Schema Essentials

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| email | String(255) | UNIQUE, INDEXED |
| first_name | String(100) | INDEXED |
| last_name | String(100) | |
| phone | String(20) | Optional |
| address | String(255) | Optional |
| city | String(100) | Optional |
| state | String(100) | Optional |
| zip_code | String(20) | Optional |
| date_of_birth | String(20) | ISO 8601 |
| enrollment_date | DateTime | Timezone aware |
| is_active | Boolean | Default TRUE, INDEXED |
| notes | Text | Optional |
| submitted_via_form | Boolean | Tracks source |
| form_submission_code | String(50) | UNIQUE for public forms |
| created_at | DateTime | Auto timestamp |
| updated_at | DateTime | Auto timestamp |

## 🎨 UI Components

### AdminStudentsWidget
- **Shows**: Student table with all details
- **Actions**: Add, Edit, Delete, Search
- **Permissions**: `students:write` required
- **Location**: Dashboard

### ShareStudentForm
- **Shows**: Public registration form
- **Actions**: Fill form, Submit, Get confirmation code
- **Permissions**: None (public)
- **Location**: `/student-form`

## 🔄 Form Submission Flow

```
1. Student fills ShareStudentForm
   ↓
2. Submits to /api/v1/students/public/submit-form
   ↓
3. Server creates Student record with:
   - submitted_via_form = TRUE
   - Unique form_submission_code
   ↓
4. User sees success page with code
   ↓
5. Code can be checked via form-status endpoint
```

## 📋 Status Badges

| Badge | Color | Meaning |
|-------|-------|---------|
| 🟢 Active | Green | Student is active |
| 🔴 Inactive | Red | Student inactive |
| 📋 Form | Blue | Submitted via public form |
| ✏️ Manual | Orange | Added by admin manually |

## 🚀 Getting Started

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
docker-compose up
```

### 2. Frontend Setup
```bash
cd students_data_store
npm install
npm run dev
```

### 3. Test Admin
- Login: admin@example.com / admin123
- Go to Dashboard
- Find "Student Management" widget
- Add/Edit/Delete students

### 4. Test Public Form
- Visit: localhost:5173/student-form
- Fill and submit form
- Get confirmation code

## 💡 Tips & Tricks

1. **Search is real-time** - Type name or email to filter
2. **Form validation** - Required fields marked with *
3. **Edit inline** - Click pencil icon to edit any student
4. **Delete safe** - Confirmation required before deletion
5. **Mobile friendly** - Responsive design included
6. **Audit trail** - All changes logged (view in Audit Logs widget)

## ⚠️ Important Notes

- Email must be unique (enforced at DB level)
- Public form submissions are tracked separately
- All timestamps are in UTC
- Admin must have `students:write` permission to see widget
- Deleting student is permanent (archived in audit log)

---

**Last Updated:** April 8, 2026
**System Version:** 1.0.0
