from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/teacher", tags=["Teacher"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "teacher": return RedirectResponse("/login")
    my_courses = db.query(models.Course).filter(models.Course.teacher_id == user.user_id).all()
    return templates.TemplateResponse("dashboard_teacher.html", {"request": request, "user": user, "courses": my_courses})

@router.get("/course/{course_id}", response_class=HTMLResponse)
async def manage_course(course_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "teacher": return RedirectResponse("/login")
    course = db.query(models.Course).filter(models.Course.course_id == course_id, models.Course.teacher_id == user.user_id).first()
    if not course: return HTMLResponse("<h1>Không tìm thấy khóa học.</h1>", status_code=404)
    return templates.TemplateResponse("teacher_course_detail.html", {"request": request, "user": user, "course": course})

@router.post("/add_lesson")
async def add_lesson(course_id: int = Form(...), title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    new_lesson = models.Lesson(title=title, content=content, course_id=course_id)
    db.add(new_lesson)
    db.commit()
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/add_quiz")
async def add_quiz(course_id: int = Form(...), lesson_id: int = Form(...), title: str = Form(...), duration: int = Form(...), db: Session = Depends(get_db)):
    new_quiz = models.Quiz(title=title, duration=duration, lesson_id=lesson_id, course_id=course_id)
    db.add(new_quiz)
    db.commit()
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def manage_quiz(quiz_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "teacher": return RedirectResponse("/login")
    
    quiz = db.query(models.Quiz).filter(models.Quiz.quiz_id == quiz_id).first()
    if not quiz: return HTMLResponse("<h1>Không tìm thấy Quiz này</h1>", status_code=404)
        
    return templates.TemplateResponse("teacher_quiz_detail.html", {"request": request, "user": user, "quiz": quiz})

@router.post("/add_question")
async def add_question(
    quiz_id: int = Form(...),
    content: str = Form(...),
    option_a: str = Form(...), option_b: str = Form(...), option_c: str = Form(...), option_d: str = Form(...),
    correct_answer: str = Form(...),
    db: Session = Depends(get_db)
):
    new_q = models.Question(
        quiz_id=quiz_id, content=content, question_type="mcq",
        option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d,
        correct_answer=correct_answer
    )
    db.add(new_q)
    db.commit()
    return RedirectResponse(url=f"/teacher/quiz/{quiz_id}", status_code=302)

@router.post("/delete_lesson")
async def delete_lesson(
    lesson_id: int = Form(...),
    course_id: int = Form(...),
    db: Session = Depends(get_db)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.lesson_id == lesson_id).first()
    if lesson:
        quizzes = db.query(models.Quiz).filter(models.Quiz.lesson_id == lesson_id).all()
        for q in quizzes:
            db.query(models.Question).filter(models.Question.quiz_id == q.quiz_id).delete()
            db.query(models.QuizSubmission).filter(models.QuizSubmission.quiz_id == q.quiz_id).delete()
            db.delete(q)
        
        db.delete(lesson)
        db.commit()
        
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/delete_quiz")
async def delete_quiz(
    quiz_id: int = Form(...),
    course_id: int = Form(...),
    db: Session = Depends(get_db)
):
    db.query(models.Question).filter(models.Question.quiz_id == quiz_id).delete()
    
    db.query(models.QuizSubmission).filter(models.QuizSubmission.quiz_id == quiz_id).delete()
    
    db.query(models.Quiz).filter(models.Quiz.quiz_id == quiz_id).delete()
    db.commit()
    
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/send_notification")
async def send_notification_to_students(
    course_id: int = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    course = db.query(models.Course).filter(
        models.Course.course_id == course_id, 
        models.Course.teacher_id == user.user_id
    ).first()
    
    if not course:
        return HTMLResponse("Lỗi: Bạn không có quyền gửi thông báo ở khóa này.", status_code=403)

    payments = db.query(models.Payment).filter(
        models.Payment.course_id == course_id
    ).all()

    if not payments:
        return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

    count = 0
    formatted_message = f"[{course.title}]: {message}"

    for payment in payments:
        new_notif = models.Notification(
            user_id=payment.student_id, 
            message=formatted_message,
            is_read=False
        )
        db.add(new_notif)
        count += 1

    db.commit()

    print(f"Đã gửi thông báo đến {count} học sinh.")
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)