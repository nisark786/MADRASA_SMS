-- Migration: Add database indexes for foreign keys and query optimization
-- Purpose: Improve query performance on frequently accessed columns
-- Created: 2026-04-11

-- Foreign Key Indexes (for JOIN operations)
CREATE INDEX IF NOT EXISTS ix_user_role_user_id ON user_role(user_id);
CREATE INDEX IF NOT EXISTS ix_user_role_role_id ON user_role(role_id);

CREATE INDEX IF NOT EXISTS ix_role_permission_role_id ON role_permission(role_id);
CREATE INDEX IF NOT EXISTS ix_role_permission_permission_id ON role_permission(permission_id);

CREATE INDEX IF NOT EXISTS ix_widget_permission_widget_id ON widget_permission(widget_id);
CREATE INDEX IF NOT EXISTS ix_widget_permission_permission_id ON widget_permission(permission_id);

CREATE INDEX IF NOT EXISTS ix_form_submission_form_id ON form_submission(form_link_id);

-- Query Optimization Indexes (for WHERE clauses)
CREATE INDEX IF NOT EXISTS ix_student_email ON student(email);
CREATE INDEX IF NOT EXISTS ix_student_admission_no ON student(admission_no);

CREATE INDEX IF NOT EXISTS ix_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS ix_user_is_active ON "user"(is_active);

CREATE INDEX IF NOT EXISTS ix_form_link_token ON form_link(token);
CREATE INDEX IF NOT EXISTS ix_form_link_is_active ON form_link(is_active);

CREATE INDEX IF NOT EXISTS ix_form_submission_status ON form_submission(status);

-- Composite Indexes (for common filter combinations)
CREATE INDEX IF NOT EXISTS ix_student_class_created ON student(class_name, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_form_submission_form_status ON form_submission(form_link_id, status);

-- Indexes for sorting operations
CREATE INDEX IF NOT EXISTS ix_student_created_at_desc ON student(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_form_submission_created_at_desc ON form_submission(created_at DESC);

-- Note: These indexes will significantly improve performance on:
-- - User lookups by email (login, search)
-- - Student lookups by email or admission number (duplication checks)
-- - Form queries by token (public form access)
-- - Submission queries by status (filtering)
-- - JOIN operations between user/role/permission
-- - Sorted queries (list endpoints with ORDER BY)
