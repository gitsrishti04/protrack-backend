from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)  # protect API
):
    role = user.get("role")
    email = user.get("sub")   # JWT stores email under 'sub'

    if role == "team_lead":
        # Only projects where this team lead is a member (matched by email)
        member_rows = db.query(ProjectMember).filter(
            ProjectMember.email == email
        ).all()
        project_ids = list({m.project_id for m in member_rows})
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    else:
        # Admins / super_admin see everything
        projects = db.query(Project).all()

    total = len(projects)
    completed = len([p for p in projects if p.status == "completed"])
    delayed = len([p for p in projects if p.status == "delayed"])
    on_track = len([p for p in projects if p.status == "on_track"])

    return {
        "total": total,
        "completed": completed,
        "delayed": delayed,
        "on_track": on_track,
        "role": role    # pass role through so frontend can branch if needed
    }

@router.get("/workload")
def get_workload(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Total tasks across all projects
    from app.models.task import Task
    tasks = db.query(Task).all()
    
    # Group by assigned_to
    workload = {}
    for t in tasks:
        if t.assigned_to:
            workload[t.assigned_to] = workload.get(t.assigned_to, 0) + 1
            
    # Format for Recharts pie chart: { name: "Member", value: count, tasks: count }
    result = []
    for name, count in workload.items():
        result.append({
            "name": name,
            "value": count,
            "tasks": count
        })
        
    return result


@router.get("/resource-utilization")
def get_resource_utilization(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Returns per-project resource utilization:
    - project name
    - total members assigned
    - total tasks
    - completed tasks
    - delayed tasks
    - utilization % (completed / total tasks * 100)
    """
    from app.models.task import Task

    projects  = db.query(Project).all()
    tasks     = db.query(Task).all()
    members   = db.query(ProjectMember).all()

    # Index by project_id
    tasks_by_project   = {}
    for t in tasks:
        tasks_by_project.setdefault(t.project_id, []).append(t)

    members_by_project = {}
    for m in members:
        members_by_project.setdefault(m.project_id, []).append(m)

    result = []
    for p in projects:
        ptasks   = tasks_by_project.get(p.id, [])
        pmembers = members_by_project.get(p.id, [])

        total     = len(ptasks)
        completed = len([t for t in ptasks if t.status == "completed"])
        delayed   = len([t for t in ptasks if t.status == "delayed"])
        in_prog   = len([t for t in ptasks if t.status == "in_progress"])
        utilization = round((completed / total * 100) if total > 0 else 0)

        result.append({
            "project":      p.name,
            "members":      len(pmembers),
            "total_tasks":  total,
            "completed":    completed,
            "in_progress":  in_prog,
            "delayed":      delayed,
            "utilization":  utilization,
            "status":       p.status,
        })

    # Sort by members descending (highest workload first)
    result.sort(key=lambda x: x["members"], reverse=True)
    return result


@router.get("/progress-over-time")
def get_progress_over_time(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Returns average project completion grouped by month
    based on real progress history entries in the DB.
    Falls back to current project completion if no history exists.
    """
    from app.models.progress_history import ProgressHistory
    from sqlalchemy import func

    # Try real history data first
    rows = (
        db.query(
            func.to_char(ProgressHistory.updated_at, 'Mon YYYY').label("month"),
            func.avg(ProgressHistory.progress).label("progress"),
            func.min(ProgressHistory.updated_at).label("sort_key"),
        )
        .group_by(func.to_char(ProgressHistory.updated_at, 'Mon YYYY'))
        .order_by(func.min(ProgressHistory.updated_at))
        .limit(12)
        .all()
    )

    if rows:
        return [
            {"month": r.month, "progress": round(r.progress)}
            for r in rows
        ]

    # Fallback: use current project completion as a single data point
    projects = db.query(Project).all()
    if not projects:
        return []

    avg = round(sum(p.completion for p in projects) / len(projects))
    from datetime import datetime
    return [{"month": datetime.now().strftime("%b %Y"), "progress": avg}]
