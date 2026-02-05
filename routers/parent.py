from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/parent", tags=["Parent"])
templates = Jinja2Templates(directory="templates")

def verify_parent(user: models.User = Depends(get_current_user)):
    if not user or user.role != "parent":
        raise HTTPException(status_code=403, detail="Chỉ dành cho Phụ huynh.")
    return user

@router.get("/", response_class=HTMLResponse)
async def parent_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_parent)):
    parent = user.parent_profile
    if not parent: return "Lỗi: Tài khoản chưa có hồ sơ Phụ huynh."

    children = parent.children 

    notifs = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id
    ).order_by(desc(models.Notification.created_at)).limit(5).all()

    unread_count = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False
    ).count()

    return templates.TemplateResponse("parent_dashboard.html", {
        "request": request, 
        "user": user, 
        "children": children,
        "notifications": notifs,
        "unread_count": unread_count
    })

@router.get("/child/{student_id}", response_class=HTMLResponse)
async def monitor_child(student_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_parent)):
    parent = user.parent_profile
    
    child = db.query(models.Student).filter(
        models.Student.student_id == student_id,
        models.Student.parent_id == parent.parent_id
    ).first()
    
    if not child:
        return RedirectResponse("/parent?msg=access_denied")

    courses = db.query(models.Course).join(models.Payment).filter(
        models.Payment.student_id == child.student_id,
        models.Payment.status == 'paid'
    ).all()

    quiz_results = db.query(models.QuizSubmission).filter(
        models.QuizSubmission.student_id == child.student_id
    ).order_by(desc(models.QuizSubmission.submitted_at)).limit(10).all()

    assignments = db.query(models.Submission).filter(
        models.Submission.student_id == child.student_id
    ).order_by(desc(models.Submission.submitted_at)).limit(10).all()

    unread_count = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False
    ).count()

    return templates.TemplateResponse("parent_child_detail.html", {
        "request": request, 
        "user": user, 
        "child": child,
        "courses": courses,
        "quiz_results": quiz_results,
        "assignments": assignments,
        "unread_count": unread_count
    })

@router.get("/alerts", response_class=HTMLResponse)
async def parent_alerts(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_parent)):
    notifs = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id
    ).order_by(desc(models.Notification.created_at)).all()
    
    for n in notifs:
        if not n.is_read: n.is_read = True
    db.commit()

    return templates.TemplateResponse("parent_alerts.html", {
        "request": request, 
        "user": user, 
        "notifications": notifs,
        "unread_count": 0
    })