from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/profile", tags=["Profile"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def view_profile(
    request: Request, 
    user: models.User = Depends(get_current_user),
    msg: str = None
):
    if not user:
        return RedirectResponse("/login")
        
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "msg": msg
    })

@router.post("/update")
async def update_profile(
    request: Request,
    fullname: str = Form(...),
    password: str = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse("/login")

    user.fullname = fullname.strip()
    
    if password and password.strip():
        user.password_hash = password.strip()
        
    db.commit()
    db.refresh(user)
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": user, 
        "msg": "Cập nhật thông tin thành công!"
    })