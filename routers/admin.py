from typing import List, Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, or_ 
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

def verify_admin(user: models.User = Depends(get_current_user)):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")
    return user

@router.get("/financials", response_class=HTMLResponse)
async def manage_financials(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_admin)):
    total_revenue = db.query(func.sum(models.Payment.amount)).scalar() or 0
    transactions = db.query(models.Payment).order_by(models.Payment.payment_date.desc()).all()
    
    return templates.TemplateResponse("admin_financials.html", {
        "request": request,
        "user": user,
        "total_revenue": round(total_revenue, 2),
        "transactions": transactions
    })

@router.get("/users", response_class=HTMLResponse)
async def manage_users(
    request: Request, 
    search: str = "",
    db: Session = Depends(get_db), 
    user: models.User = Depends(verify_admin)
):
    query = db.query(models.User)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.User.fullname.like(search_term),
                models.User.email.like(search_term)
            )
        )
    
    users = query.all()
    
    all_students = db.query(models.Student).join(models.User).filter(models.User.role == 'student').all() 

    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": user,
        "users": users,
        "all_students": all_students,
        "search_query": search
    })

@router.post("/users/role")
async def update_user_role(
    user_id: int = Form(...), 
    new_role: str = Form(...), 
    child_ids: Optional[List[int]] = Form(None), 
    db: Session = Depends(get_db), 
    user: models.User = Depends(verify_admin)
):
    target_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    if not target_user:
        return RedirectResponse(url="/admin/users?error=UserNotFound", status_code=302)
    
    if target_user.user_id == user.user_id:
        return RedirectResponse(url="/admin/users?error=CannotChangeSelf", status_code=302)

    target_user.role = new_role

    if new_role == 'student':
        if not target_user.student_profile:
            new_profile = models.Student(
                student_id=user_id, 
                student_code=f"HS{user_id:04d}", 
                grade_level="Chưa cập nhật"
            )
            db.add(new_profile)

    elif new_role == 'teacher':
        if not target_user.teacher_profile:
            new_profile = models.Teacher(
                teacher_id=user_id, 
                teacher_code=f"GV{user_id:04d}", 
                specialization="Chưa cập nhật"
            )
            db.add(new_profile)

    elif new_role == 'parent':
        if not target_user.parent_profile:
            new_profile = models.Parent(
                parent_id=user_id, 
                phone_number=""
            )
            db.add(new_profile)
            db.flush() 
        
        parent_profile = target_user.parent_profile or db.query(models.Parent).filter(models.Parent.parent_id == user_id).first()

        if parent_profile:
            parent_profile.children.clear()
            if child_ids:
                selected_students = db.query(models.Student).filter(models.Student.student_id.in_(child_ids)).all()
                for student in selected_students:
                    parent_profile.children.append(student)

    db.commit()
    return RedirectResponse(url="/admin/users?msg=updated", status_code=302)


@router.post("/users/delete")
async def delete_user(user_id: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_admin)):
    target_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    if target_user and target_user.user_id != user.user_id:
        if target_user.role == 'student':
            db.query(models.Student).filter(models.Student.student_id == user_id).delete()
        elif target_user.role == 'teacher':
            db.query(models.Teacher).filter(models.Teacher.teacher_id == user_id).delete()
        elif target_user.role == 'parent':
            db.query(models.Parent).filter(models.Parent.parent_id == user_id).delete()
            
        db.delete(target_user)
        db.commit()
        
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/settings", response_class=HTMLResponse)
async def configure_system(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_admin)):
    settings = {
        "maintenance_mode": False,
        "allow_registration": True,
        "default_currency": "USD"
    }
    return templates.TemplateResponse("admin_settings.html", {
        "request": request, "user": user, "settings": settings
    })