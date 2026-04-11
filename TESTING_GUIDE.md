# 🧪 Testing Guide - Students Management System

## 📋 Pre-Test Setup

### 1. Start Backend
```bash
cd backend
docker-compose up -d
```

Wait for startup messages:
```
✅ Redis connected
✅ Database tables ready
✅ Seed complete — admin can now create roles & users dynamically
```

### 2. Start Frontend
```bash
cd students_data_store
npm run dev
```

Frontend should be available at: `http://localhost:5173`

---

## 🧑‍💼 Test 1: Admin Student Management

### Setup
1. Go to `http://localhost:5173/login`
2. Use credentials:
   ```
   Email: admin@example.com
   Password: admin123
   ```
3. Click "Sign In"

### Expected Result
- ✅ Redirected to `/dashboard`
- ✅ Page title shows "Dashboard"
- ✅ Greeting shows "Welcome back, System Admin"

### Continue Testing
1. Look for widget titled **"Student Management"**
2. Should show "0 students" badge initially

---

## ➕ Test 2: Add Student

### Steps
1. Click **"➕ Add Student"** button
2. Modal form should appear with title "Add New Student"

### Fill Form
```
First Name *: John
Last Name *: Doe
Email *: john.doe@example.com
Phone: +1-555-0123
Address: 123 Main Street
City: New York
State: NY
Zip Code: 10001
Date of Birth: 2000-01-15
Enrollment Date: 2026-01-15
Notes: Test student for admin workflow
```

### Submit
1. Click **"Create Student"** button
2. Modal should close
3. Table should refresh
4. Badge should now show **"1 students"**
5. New student appears in table

### Expected Data in Table
```
Name: John Doe
Email: john.doe@example.com
Phone: +1-555-0123
City: New York
Type: ✏️ Manual
```

---

## ✏️ Test 3: Edit Student

### Steps
1. Find "John Doe" in the table
2. Click **✏️ Edit** button (pencil icon)
3. Modal should appear with title "Edit Student"

### Make Changes
```
Phone: +1-555-9999 (change last 4 digits)
Notes: Updated test student
```

### Save
1. Click **"Update Student"** button
2. Modal closes
3. Table refreshes
4. Changes should be reflected

### Verify
- Phone number updated in table
- Last student entry in audit logs shows UPDATE_STUDENT

---

## 🔍 Test 4: Search Functionality

### Steps
1. Go back to Student Management widget
2. Look for search bar at top: "Search by name or email..."

### Test Searches
```
Search for: "john"
→ Should show: John Doe entry
→ Others filtered out

Search for: "doe@"
→ Should show: John Doe entry

Search for: "xyz"
→ Should show: No results / Empty state
```

### Expected Behavior
- Real-time filtering as you type
- Case-insensitive search
- Searches both name and email

---

## 🗑️ Test 5: Delete Student

### Steps
1. Find "John Doe" in table
2. Click **🗑️ Delete** button (trash icon)
3. Browser confirmation dialog appears

### Confirm Delete
1. Click "OK" in confirmation
2. Modal closes
3. Table refreshes
4. Student removed from list
5. Badge updates to "0 students"

### Verify Deletion
- Entry removed from UI
- Audit log shows DELETE_STUDENT action

---

## 👥 Test 6: Add Multiple Students

### Create 3 More Students
Use the form to add:

**Student 2:**
```
John: Jane
Last: Smith
Email: jane.smith@example.com
City: Los Angeles
```

**Student 3:**
```
First: Michael
Last: Johnson
Email: michael.j@example.com
City: Chicago
```

**Student 4:**
```
First: Sarah
Last: Williams
Email: sarah.w@example.com
City: Boston
```

### Expected Result
- All 3 students appear in table
- Badge shows "3 students"
- Search works across all entries

---

## 📋 Test 7: Public Form Submission

### Access Public Form
1. Open new tab
2. Go to: `http://localhost:5173/student-form`

### Expected View
- Beautiful form with "📋 Student Registration" title
- "Submit your information" subtitle
- All form fields visible

### Fill Form
```
First Name *: Alex
Last Name *: Thompson
Email *: alex.thompson@email.com
Phone: +1-555-1234
Address: 456 Oak Avenue
City: San Francisco
State: CA
Zip Code: 94102
Date of Birth: 1999-05-20
Notes: From public form submission
```

### Submit
1. Click **"📤 Submit Application"** button
2. Loading spinner appears
3. After 2-3 seconds, success page shows

### Expected Success Page
```
✅ Thank You!
Your information has been received

"Thank you for submitting your information..."

Your submission code: [RANDOM CODE]
(e.g., "AB3F7K2Q")

[Home] [Submit Another]
```

### Save Code
- Note down the submission code
- Will be used for verification

---

## 📊 Test 8: Verify Form Submission in Admin Panel

### Go Back to Admin
1. Switch to admin tab (or go to `/dashboard`)
2. Go to Student Management widget
3. Badge should now show **"4 students"**

### Check New Entry
Look for: Alex Thompson
```
Name: Alex Thompson
Email: alex.thompson@email.com
Phone: +1-555-1234
City: San Francisco
Type: 📋 Form  ← Should show FORM, not Manual!
```

### Key Difference
- Admin-created: "✏️ Manual"
- Form-submitted: "📋 Form"

---

## 🔄 Test 9: Multiple Form Submissions

### Submit Another Student via Form
1. Go back to form tab
2. Click **"Submit Another"** button
3. Form resets
4. Fill new student info:

```
First: Blake
Last: Davis
Email: blake.d@mail.com
Phone: +1-555-5678
City: Denver
```

5. Submit again
6. New confirmation code received

### Verify in Admin
- Back to dashboard
- Badge shows "5 students"
- Blake Davis appears with "📋 Form" type

---

## 🔐 Test 10: Permission Verification

### Test Protection (Optional)
If you have another user with limited permissions:

1. Create a user with only `students:read` permission
2. Login with that user
3. Go to dashboard

### Expected Behavior
- "Student Management" widget NOT visible (requires `students:write`)
- "Students Table" widget IS visible (requires `students:read`)

---

## 📱 Test 11: Responsive Design

### On Desktop
- Form displays in 2-column grid
- Table shows all columns
- Modal properly centered

### On Mobile/Tablet
1. Resize browser to 768px width
2. Form should stack to single column
3. Table should be scrollable
4. Modal should fit screen

---

## 🐛 Test 12: Error Handling

### Test Duplicate Email
1. Try adding student with existing email
2. Error message appears: "Email already exists"
3. Form stays open for correction

### Test Missing Required Fields
1. Try submitting form with blank required fields
2. Browser validation: "Please fill out this field"
3. Or backend error if bypassed

### Test Invalid Email
1. Enter invalid email: "not-an-email"
2. Validation error appears

---

## 📊 Test 13: Audit Logging

### Check Audit Log Widget
1. Go to dashboard
2. Find "Audit Logs" widget
3. Scroll through entries

### Expected Log Entries
```
CREATE_STUDENT - John Doe (Manual)
UPDATE_STUDENT - John Doe (by Admin)
CREATE_STUDENT - Jane Smith (Manual)
...
```

---

## 🎯 Final Checklist

After all tests, verify:

- [x] Admin can view students list
- [x] Admin can add new student via modal form
- [x] Admin can edit student details
- [x] Admin can delete student with confirmation
- [x] Search filters students in real-time
- [x] Public form accessible without login
- [x] Public form creates student record
- [x] Submission code generated and displayed
- [x] Form submissions tracked (shows "📋 Form" badge)
- [x] Manual entries tracked (shows "✏️ Manual" badge)
- [x] Multiple form submissions work
- [x] Student count badge updates correctly
- [x] Audit logs record all actions
- [x] Permission-based access (if testing multiple users)
- [x] Responsive design works

---

## 🔧 Troubleshooting

### Issue: "Student Management" widget not showing
**Solution:**
- Verify user has `students:write` permission
- Check browser console for errors
- Restart backend

### Issue: Form submission fails
**Solution:**
- Check backend logs: `docker logs students_backend`
- Verify email is unique
- Check network tab in DevTools

### Issue: Changes not appearing in table
**Solution:**
- Manually refresh page (F5)
- Check browser console for JS errors
- Verify backend is running

### Issue: Database connection error
**Solution:**
- Check Supabase is accessible
- Verify DATABASE_URL in docker-compose.yml
- Check Docker logs

---

## 📊 Expected Database State After Tests

```sql
SELECT * FROM students;

-- Should have ~5 rows:
1. John Doe (updated) - Manual
2. Jane Smith - Manual
3. Michael Johnson - Manual
4. Sarah Williams - Manual
5. Alex Thompson - Form
6. Blake Davis - Form

-- Check submitted_via_form and form_submission_code:
-- Form submissions should have form_submission_code (non-null)
-- Manual entries should have form_submission_code = NULL
```

---

## ✅ Success Indicators

All tests passed when you see:

1. **Admin widget** working with full CRUD
2. **Public form** submitting successfully
3. **Student count** updating correctly
4. **Submission codes** generated and displayed
5. **Audit logs** recording all actions
6. **Type badges** distinguishing form vs manual
7. **Search** filtering in real-time
8. **No errors** in console or backend logs

---

## 📞 Still Having Issues?

Check:
1. Backend logs: `docker logs students_backend`
2. Frontend console: DevTools → Console tab
3. API: Visit `http://localhost:8000/docs` for Swagger UI
4. Database: Check Supabase dashboard for table data

---

**Testing Version:** 1.0.0  
**Last Updated:** April 8, 2026
