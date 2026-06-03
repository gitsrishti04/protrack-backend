from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.routes.auth import get_db
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate
from app.schemas.member import MemberCreate  # NEW

from app.models.project import Project
from app.models.task import Task
from app.models.project_member import ProjectMember  # NEW

from app.utils.deps import get_current_user

router = APIRouter()

# =========================
# CREATE PROJECT
# =========================
@router.post("/projects")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        completion=project.completion,
        deadline=project.deadline,
        team=project.team
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


# =========================
# GET ALL PROJECTS (role-scoped, paginated, searchable, filterable by status)
# =========================
@router.get("/projects")
def get_projects(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    status: str = "",
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    role = user.get("role")
    email = user.get("sub")

    query = db.query(Project)

    if role == "team_lead":
        member_rows = db.query(ProjectMember).filter(ProjectMember.email == email).all()
        project_ids = list({m.project_id for m in member_rows})
        if not project_ids:
            return {"items": [], "total": 0}
        query = query.filter(Project.id.in_(project_ids))

    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    if status and status != "all":
        query = query.filter(Project.status == status)

    total = query.count()
    offset = (page - 1) * limit
    projects = query.offset(offset).limit(limit).all()

    return {
        "items": projects,
        "total": total
    }


# =========================
# GET SINGLE PROJECT
# =========================
@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


# =========================
# GET TASKS
# =========================
@router.get("/projects/{project_id}/tasks")
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return db.query(Task).filter(Task.project_id == project_id).all()


# =========================
# CREATE TASK
# =========================
@router.post("/projects/{project_id}/tasks")
def create_task(
    project_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        project_id=project_id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# =========================
# UPDATE TASK STATUS
# =========================
@router.put("/tasks/{task_id}/status")
def update_status(
    task_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = status
    db.commit()

    return task


# =========================
# PROJECT ANALYTICS
# =========================
@router.get("/projects/{project_id}/analytics")
def get_project_analytics(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "completed"])

    completion = (completed_tasks / total_tasks) * 100 if total_tasks else 0

    deadline = project.deadline
    if isinstance(deadline, str):
        deadline = datetime.strptime(deadline, "%Y-%m-%d")

    days_left = (deadline - datetime.utcnow()).days if deadline else 0

    members = list(set([t.assigned_to for t in tasks if t.assigned_to]))
    team_size = len(members)

    active_tasks = len([t for t in tasks if t.status == "in_progress"])
    delayed_tasks = len([t for t in tasks if t.status == "delayed"])

    if total_tasks == 0:
        risk = "Low"
    elif delayed_tasks > total_tasks * 0.5:
        risk = "High"
    elif delayed_tasks > 0:
        risk = "Medium"
    else:
        risk = "Low"

    return {
        "completion": round(completion, 2),
        "days_left": days_left,
        "team_size": team_size,
        "active_tasks": active_tasks,
        "risk": risk,
        "members": members,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks
    }


# =========================
# ADD MEMBER (FIXED)
# =========================
@router.post("/projects/{project_id}/members")
def add_member(
    project_id: int,
    member: MemberCreate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_member = ProjectMember(
        project_id=project_id,
        name=member.name,
        role=member.role,
        email=member.email   # link to team_lead user account
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member


# =========================
# GET MEMBERS (FIXED)
# =========================
@router.get("/projects/{project_id}/members")
def get_members(
    project_id: int,
    db: Session = Depends(get_db)
):
    return db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()


from fastapi import Body

# =========================
# =========================
# UPDATE PROJECT PROGRESS (also saves to history)
# =========================
@router.put("/projects/{project_id}/progress")
def update_project_progress(
    project_id: int,
    progress: int = Body(..., embed=True),
    task_name: str = Body(None, embed=True),
    comments: str = Body(None, embed=True),
    status: str = Body(None, embed=True),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    from app.models.progress_history import ProgressHistory

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only team lead / admin can update
    if user.get("role") not in ["team_lead", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    # Update project completion
    project.completion = progress
    if status:
        project.status = status

    # Save history entry to DB
    history_entry = ProgressHistory(
        project_id=project_id,
        progress=progress,
        task_name=task_name or "Progress update",
        comments=comments or "",
        status=status or project.status,
        updated_at=datetime.utcnow(),
    )
    db.add(history_entry)
    db.commit()
    db.refresh(project)

    return project


# =========================
# GET PROGRESS HISTORY
# =========================
@router.get("/projects/{project_id}/history")
def get_progress_history(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    from app.models.progress_history import ProgressHistory

    entries = (
        db.query(ProgressHistory)
        .filter(ProgressHistory.project_id == project_id)
        .order_by(ProgressHistory.updated_at.asc())
        .all()
    )

    return [
        {
            "id":         e.id,
            "progress":   e.progress,
            "task_name":  e.task_name,
            "comments":   e.comments,
            "status":     e.status,
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        }
        for e in entries
    ]


# =========================
# DELETE TASK
# =========================
@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"detail": "Task deleted"}


# =========================
# DELETE MEMBER
# =========================
@router.delete("/projects/{project_id}/members/{member_id}")
def delete_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()

    return {"detail": "Member deleted"}