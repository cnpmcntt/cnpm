from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "admin": 
        return RedirectResponse("/login")
    
    users = db.query(models.User).all()
    courses = db.query(models.Course).all()
    payments = db.query(models.Payment).all()
    
    teachers = db.query(models.User).filter(models.User.role == 'teacher').all()
    
    return templates.TemplateResponse("dashboard_admin.html", {
        "request": request, 
        "user": user, 
        "users": users, 
        "courses": courses, 
        "payments": payments,
        "teachers": teachers
    })

@router.post("/change_role")
async def change_role(user_id: int = Form(...), new_role: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user: return HTMLResponse(content="Lỗi: User not found", status_code=404)

    if user.role == new_role: return RedirectResponse(url="/admin", status_code=302)

    try:
        if user.role == "student":
            db.query(models.Student).filter(models.Student.student_id == user_id).delete()
        elif user.role == "teacher":
            db.query(models.Teacher).filter(models.Teacher.teacher_id == user_id).delete()
        
        db.flush() 

        if new_role == "student":
            existing = db.query(models.Student).filter(models.Student.student_id == user_id).first()
            if not existing:
                db.add(models.Student(student_id=user_id, student_code=f"HS_{user_id}", grade_level="IGCSE 10"))
        elif new_role == "teacher":
            existing = db.query(models.Teacher).filter(models.Teacher.teacher_id == user_id).first()
            if not existing:
                db.add(models.Teacher(teacher_id=user_id, teacher_code=f"GV_{user_id}", specialization="General"))

        user.role = new_role
        db.commit()
    except Exception as e:
        db.rollback()
        return HTMLResponse(content=f"Lỗi: {e}", status_code=500)
    
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/add_course")
async def add_course(
    title: str = Form(...), 
    price: float = Form(...), 
    teacher_id: int = Form(...), 
    db: Session = Depends(get_db)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.teacher_id == teacher_id).first()
    if not teacher:
         return HTMLResponse(content="Lỗi: ID này không phải Giáo viên.", status_code=400)

    new_course = models.Course(
        title=title, 
        price=price, 
        teacher_id=teacher_id, 
    )
    db.add(new_course)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/delete_course")
async def delete_course(
    course_id: int = Form(...), 
    db: Session = Depends(get_db)
):
    course = db.query(models.Course).filter(models.Course.course_id == course_id).first()
    if not course:
        return HTMLResponse(content="Lỗi: Không tìm thấy khóa học.", status_code=404)

    try:
        db.query(models.Payment).filter(models.Payment.course_id == course_id).delete()

        assignments = db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()
        for assign in assignments:
            db.query(models.Submission).filter(models.Submission.assignment_id == assign.assignment_id).delete()
            db.delete(assign)

        lessons = db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()
        for lesson in lessons:
            quizzes = db.query(models.Quiz).filter(models.Quiz.lesson_id == lesson.lesson_id).all()
            for quiz in quizzes:
                db.query(models.Question).filter(models.Question.quiz_id == quiz.quiz_id).delete()
                db.query(models.QuizSubmission).filter(models.QuizSubmission.quiz_id == quiz.quiz_id).delete()
                db.delete(quiz)
            
            db.delete(lesson)

        orphan_quizzes = db.query(models.Quiz).filter(models.Quiz.course_id == course_id).all()
        for quiz in orphan_quizzes:
            db.query(models.Question).filter(models.Question.quiz_id == quiz.quiz_id).delete()
            db.query(models.QuizSubmission).filter(models.QuizSubmission.quiz_id == quiz.quiz_id).delete()
            db.delete(quiz)

        db.delete(course)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"LỖI XÓA KHÓA HỌC: {e}")
        return HTMLResponse(content=f"<h1>Lỗi không thể xóa khóa học</h1><p>{e}</p><a href='/admin'>Quay lại</a>", status_code=500)

    return RedirectResponse(url="/admin", status_code=302)