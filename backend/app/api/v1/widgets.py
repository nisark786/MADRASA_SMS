from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict

from app.core.database import get_db
from app.core import redis_client as rc
from app.models.user import User
from app.models.widget import Widget, WidgetPermission
from app.models.permission import Permission
from app.dependencies.auth import get_current_user, get_user_permissions

router = APIRouter(prefix="/widgets", tags=["Widgets"])


@router.get("/my-widgets")
async def get_my_widgets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns widgets the current user is allowed to see.
    Cached per-user in Redis (invalidated when roles change).
    """
    cache_key = f"cache:widgets:{current_user.id}"

    cached = await rc.get_cached_response(cache_key)
    if cached is not None:
        return cached

    user_perms = await get_user_permissions(current_user.id, db)

    result = await db.execute(
        select(Widget, Permission.name.label("required_perm"))
        .outerjoin(WidgetPermission, WidgetPermission.widget_id == Widget.id)
        .outerjoin(Permission, Permission.id == WidgetPermission.permission_id)
        .where(Widget.is_active == True)
        .order_by(Widget.created_at)
    )
    rows = result.all()

    widget_map: dict[str, dict] = {}
    widget_perms: dict[str, set] = defaultdict(set)

    for widget, req_perm in rows:
        if widget.id not in widget_map:
            widget_map[widget.id] = {
                "id":             widget.id,
                "name":           widget.name,
                "display_name":   widget.display_name,
                "description":    widget.description,
                "component_key":  widget.component_key,
                "widget_type":    widget.widget_type,
                "default_config": widget.default_config,
            }
        if req_perm:
            widget_perms[widget.id].add(req_perm)

    allowed = [
        data for wid, data in widget_map.items()
        if not widget_perms[wid] or widget_perms[wid].intersection(user_perms)
    ]

    response = {"widgets": allowed, "total": len(allowed)}
    await rc.cache_response(cache_key, response, ttl=120)
    return response


@router.get("/all")
async def get_all_widgets(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Returns all widgets — cached list."""
    cache_key = "cache:widgets:all"
    cached = await rc.get_cached_response(cache_key)
    if cached is not None:
        return cached

    result = await db.execute(
        select(
            Widget.id, Widget.name, Widget.display_name,
            Widget.component_key, Widget.widget_type, Widget.is_active
        )
    )
    data = [dict(r) for r in result.mappings().all()]
    await rc.cache_response(cache_key, data, ttl=300)
    return data
