# Makes all models importable from app.models
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permission import Permission, RolePermission
from app.models.widget import Widget, WidgetPermission, UserWidgetPreference
from app.models.audit_log import AuditLog
from app.models.form import FormLink, FormSubmission
from app.models.student import Student

__all__ = [
    "User",
    "Role",
    "UserRole",
    "Permission",
    "RolePermission",
    "Widget",
    "WidgetPermission",
    "UserWidgetPreference",
    "AuditLog",
    "FormLink",
    "FormSubmission",
    "Student",
]
