"""
Bootstrap seed — runs once on startup.

Only creates the bare minimum to get started:
  ✅ All system permissions (7 granular permissions)
  ✅ One system role: "admin" (cannot be deleted)
  ✅ One admin user from environment variables
  ✅ All dashboard widgets linked to permissions

Everything else (new roles, new users, role assignments)
is created DYNAMICALLY by the admin through the API.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permission import Permission, RolePermission
from app.models.widget import Widget, WidgetPermission
from app.core.security import hash_password

# ── System permissions — these define WHAT actions exist in the system ────────
# Roles are created dynamically and pick from these permissions
SYSTEM_PERMISSIONS = [
    # module        action            display name
    ("students:read",        "students", "read",         "View student records"),
    ("students:write",       "students", "write",        "Create and edit students"),
    ("students:delete",      "students", "delete",       "Delete students"),
    ("reports:view",         "reports",  "view",         "View reports and analytics"),
    ("admin:manage_roles",   "admin",    "manage_roles", "Create and manage roles"),
    ("admin:manage_users",   "admin",    "manage_users", "Create and manage users"),
    ("admin:view_audit",     "admin",    "view_audit",   "View audit logs"),
]

# ── Widgets — linked to permissions, resolved dynamically per user ─────────────
SYSTEM_WIDGETS = [
    {
        "name":               "student_stats_card",
        "display_name":       "Student Statistics",
        "description":        "Overview card showing total students, active, inactive",
        "component_key":      "StudentStatsCard",
        "widget_type":        "card",
        "required_permission": "students:read",
    },
    {
        "name":               "student_table",
        "display_name":       "Students Table",
        "description":        "Full paginated table of all students",
        "component_key":      "StudentTableWidget",
        "widget_type":        "table",
        "required_permission": "students:read",
    },
    {
        "name":               "admin_students_panel",
        "display_name":       "Student Management",
        "description":        "Create, edit, and manage students",
        "component_key":      "AdminStudentsWidget",
        "widget_type":        "table",
        "required_permission": "students:write",
    },
    {
        "name":               "reports_chart",
        "display_name":       "Reports & Analytics",
        "description":        "Charts and data visualizations",
        "component_key":      "ReportsChartWidget",
        "widget_type":        "chart",
        "required_permission": "reports:view",
    },
    {
        "name":               "admin_users_panel",
        "display_name":       "User Management",
        "description":        "Create and manage users",
        "component_key":      "AdminUsersWidget",
        "widget_type":        "table",
        "required_permission": "admin:manage_users",
    },
    {
        "name":               "admin_roles_panel",
        "display_name":       "Role Management",
        "description":        "Create and manage roles and permissions",
        "component_key":      "AdminRolesWidget",
        "widget_type":        "form",
        "required_permission": "admin:manage_roles",
    },
    {
        "name":               "audit_log_panel",
        "display_name":       "Audit Logs",
        "description":        "View all system actions and logs",
        "component_key":      "AuditLogWidget",
        "widget_type":        "table",
        "required_permission": "admin:view_audit",
    },
]


async def seed_database(db: AsyncSession):
    print("🌱 Running database seed...")

    # ── 1. Seed system permissions ────────────────────────────────────────────
    perm_map: dict[str, Permission] = {}
    for name, module, action, desc in SYSTEM_PERMISSIONS:
        result = await db.execute(select(Permission).where(Permission.name == name))
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(name=name, module=module, action=action, description=desc)
            db.add(perm)
            await db.flush()
            print(f"  ✅ Permission created: {name}")
        perm_map[name] = perm

    # ── 2. Seed ONE system role: admin ─────────────────────────────────────────
    # NO other roles seeded — admin creates all roles dynamically via API
    result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Full system access — system role, cannot be deleted",
            is_system_role=True,   # protected from deletion
            is_active=True,
        )
        db.add(admin_role)
        await db.flush()
        print("  ✅ Admin role created")

        # Assign ALL permissions to admin role
        for perm in perm_map.values():
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        print("  ✅ All permissions assigned to admin role")

    # ── 3. Seed ONE system user (credentials from environment variables) ────────
    # NO other users seeded — admin creates all users dynamically via API
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_password:
        raise ValueError(
            "ADMIN_PASSWORD environment variable is required for initial seed. "
            "Set it before starting the application."
        )
    
    result = await db.execute(select(User).where(User.email == admin_email))
    admin_user = result.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            username="admin",
            email=admin_email,
            password_hash=hash_password(admin_password),
            first_name="System",
            last_name="Admin",
            is_active=True,
        )
        db.add(admin_user)
        await db.flush()
        db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
        print(f"  ✅ Admin user created: {admin_email}")

    # ── 4. Seed widgets (linked to permissions) ────────────────────────────────
    for wdata in SYSTEM_WIDGETS:
        result = await db.execute(select(Widget).where(Widget.name == wdata["name"]))
        widget = result.scalar_one_or_none()
        if not widget:
            widget = Widget(
                name=wdata["name"],
                display_name=wdata["display_name"],
                description=wdata["description"],
                component_key=wdata["component_key"],
                widget_type=wdata["widget_type"],
            )
            db.add(widget)
            await db.flush()

            perm = perm_map.get(wdata["required_permission"])
            if perm:
                db.add(WidgetPermission(widget_id=widget.id, permission_id=perm.id))
            print(f"  ✅ Widget created: {wdata['display_name']}")

    await db.commit()
    print("✅ Seed complete — admin can now create roles & users dynamically")
