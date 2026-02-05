from fastapi import APIRouter, Request, Form, Depends, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db
import models

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(
    request: Request, 
    response: Response, 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user or user.password_hash != password:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Email hoặc mật khẩu không chính xác!"
        })
    
    redirect_url = "/"
    if user.role == "admin": 
        redirect_url = "/admin/financials"
    elif user.role == "manager": 
        redirect_url = "/manager/dashboard"
    elif user.role == "teacher": 
        redirect_url = "/teacher"
    elif user.role == "student": 
        redirect_url = "/student"
    elif user.role == "parent": 
        redirect_url = "/parent"
    
    resp = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    
    resp.set_cookie(key="user_id", value=str(user.user_id), httponly=True)
    
    return resp

@router.get("/logout")
async def logout(response: Response):
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("user_id")
    return resp

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "error": None})

@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request, 
    email: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request, 
            "error": "Email này không tồn tại trong hệ thống!"
        })
    
    return templates.TemplateResponse("reset_password.html", {
        "request": request, 
        "user_id": user.user_id,
        "email": user.email
    })

@router.post("/reset-password")
async def reset_password_submit(
    request: Request,
    user_id: int = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if new_password != confirm_password:
        user = db.query(models.User).filter(models.User.user_id == user_id).first()
        return templates.TemplateResponse("reset_password.html", {
            "request": request, 
            "user_id": user_id,
            "email": user.email if user else "",
            "error": "Mật khẩu xác nhận không khớp!"
        })

    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user:
        user.password_hash = new_password
        db.commit()
    
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "success": "Đổi mật khẩu thành công! Vui lòng đăng nhập lại."
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
async def register_submit(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Mật khẩu xác nhận không khớp!",
            "fullname": fullname,
            "email": email
        })

    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email này đã được sử dụng! Vui lòng chọn email khác.",
            "fullname": fullname,
            "email": email
        })

    try:
        new_user = models.User(
            fullname=fullname,
            email=email,
            password_hash=password,
            role="student" 
        )
        db.add(new_user)
        db.commit()
        
        db.refresh(new_user) 

        student_code = f"HS{new_user.user_id:04d}" 
        
        new_student = models.Student(
            student_id=new_user.user_id,
            student_code=student_code,
            grade_level="Chưa cập nhật",
            parent_id=None
        )
        db.add(new_student)
        db.commit()
        
        return templates.TemplateResponse("login.html", {
            "request": request,
            "success": "Tạo tài khoản thành công! Hãy đăng nhập ngay."
        })
        
    except Exception as e:
        db.rollback()
        print(f"Lỗi đăng ký: {e}")
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Đã có lỗi xảy ra khi tạo tài khoản. Vui lòng thử lại.",
            "fullname": fullname,
            "email": email
        })