from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/manager", tags=["Manager"])
templates = Jinja2Templates(directory="templates")

def verify_manager(user: models.User = Depends(get_current_user)):
    if not user or user.role != "manager":
        raise HTTPException(status_code=403, detail="Chỉ Manager mới có quyền truy cập")
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def manager_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_manager)):
    stats = {
        "total_courses": db.query(models.Course).count(),
        "total_lessons": db.query(models.Lesson).count(),
        "total_quizzes": db.query(models.Quiz).count()
    }
    courses = db.query(models.Course).all()
    
    teachers = db.query(models.Teacher).all()

    return templates.TemplateResponse("manager_dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "courses": courses,
        "teachers": teachers
    })

@router.post("/courses/add")
async def create_course(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    teacher_id: int = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(verify_manager)
):
    new_course = models.Course(
        title=title,
        description=description,
        price=price,
        teacher_id=teacher_id,
        status="active"
    )
    db.add(new_course)
    db.commit()
    
    return RedirectResponse(url="/manager/dashboard?msg=course_created", status_code=302)

@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail(course_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_manager)):
    course = db.query(models.Course).filter(models.Course.course_id == course_id).first()
    if not course: return RedirectResponse("/manager/dashboard")
    lessons = db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()
    quizzes = db.query(models.Quiz).filter(models.Quiz.course_id == course_id).all()
    students = db.query(models.Student).join(models.Payment).filter(
        models.Payment.course_id == course_id, models.Payment.status == 'paid'
    ).all()
    return templates.TemplateResponse("manager_course_detail.html", {
        "request": request, "user": user, "course": course, "lessons": lessons, "quizzes": quizzes, "students": students
    })

@router.get("/courses", response_class=HTMLResponse)
async def view_courses_evaluation(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_manager)):
    courses = db.query(models.Course).all()
    course_evaluations = []
    for c in courses:
        student_count = len(c.payments)
        quality_status = "Tốt" if student_count >= 5 else "Cần cải thiện"
        course_evaluations.append({
            "course": c,
            "student_count": student_count,
            "quality": quality_status,
            "teacher_name": c.teacher.user.fullname if c.teacher and c.teacher.user else "Chưa có GV"
        })
    return templates.TemplateResponse("manager_courses.html", {"request": request, "user": user, "evaluations": course_evaluations})

@router.post("/send_warning")
async def send_warning_message(teacher_id: int = Form(...), course_title: str = Form(...), reason: str = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_manager)):
    message_content = f"[CẢNH BÁO] Khóa học '{course_title}' cần cải thiện. Lý do: {reason}."
    new_notif = models.Notification(user_id=teacher_id, message=message_content, is_read=False)
    db.add(new_notif)
    db.commit()
    return RedirectResponse(url="/manager/courses", status_code=status.HTTP_302_FOUND)