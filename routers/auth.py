from fastapi import APIRouter, Request, Form, Depends, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db # Import từ file dependencies
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
            "error": "Email hoặc mật khẩu sai!"
        })
    
    redirect_url = "/"
    if user.role == "admin": redirect_url = "/admin"
    elif user.role == "teacher": redirect_url = "/teacher"
    elif user.role == "student": redirect_url = "/student"
    
    resp = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    
    resp.set_cookie(key="user_id", value=str(user.user_id))
    
    return resp

@router.get("/logout")
async def logout(response: Response):
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("user_id")
    return resp