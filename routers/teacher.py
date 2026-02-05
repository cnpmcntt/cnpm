from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dependencies import get_db, get_current_user
import models

router = APIRouter(prefix="/teacher", tags=["Teacher"])
templates = Jinja2Templates(directory="templates")

def verify_teacher(user: models.User = Depends(get_current_user)):
    if not user or user.role != "teacher":
        raise HTTPException(status_code=403, detail="Chỉ Giáo viên mới có quyền này.")
    return user

@router.get("/", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    teacher = user.teacher_profile
    if not teacher: return "Lỗi: Chưa có hồ sơ giáo viên."
    
    my_courses = db.query(models.Course).filter(models.Course.teacher_id == teacher.teacher_id).all()
    
    pending_grading = db.query(models.Submission).filter(models.Submission.teacher_score == None).count()
    
    unread_notifs = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False
    ).count()

    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request, 
        "user": user, 
        "courses": my_courses, 
        "pending_count": pending_grading,
        "unread_notifs": unread_notifs
    })

@router.get("/notifications", response_class=HTMLResponse)
async def view_notifications(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    notifs = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id
    ).order_by(desc(models.Notification.created_at)).all()
    
    for n in notifs:
        if not n.is_read:
            n.is_read = True
    db.commit()

    return templates.TemplateResponse("teacher_notifications.html", {
        "request": request, "user": user, "notifications": notifs
    })

@router.get("/course/{course_id}", response_class=HTMLResponse)
async def manage_course_content(course_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    course = db.query(models.Course).filter(models.Course.course_id == course_id, models.Course.teacher_id == user.user_id).first()
    if not course: return RedirectResponse("/teacher")
    
    return templates.TemplateResponse("teacher_course_detail.html", {"request": request, "user": user, "course": course})

@router.post("/announcement/send")
async def send_announcement(
    course_id: int = Form(...), 
    message: str = Form(...), 
    db: Session = Depends(get_db), 
    user: models.User = Depends(verify_teacher)
):
    course = db.query(models.Course).filter(models.Course.course_id == course_id, models.Course.teacher_id == user.user_id).first()
    if not course: return RedirectResponse("/teacher")

    students = db.query(models.Student).join(models.Payment).filter(
        models.Payment.course_id == course_id,
        models.Payment.status == 'paid'
    ).all()

    full_message = f"[THÔNG BÁO LỚP {course.title}]: {message}"
    for stu in students:
        db.add(models.Notification(user_id=stu.user.user_id, message=full_message, is_read=False))
    
    db.commit()
    
    return RedirectResponse(url="/teacher?msg=sent_success", status_code=302)

@router.post("/lesson/add")
async def add_lesson(course_id: int = Form(...), title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    db.add(models.Lesson(title=title, content=content, course_id=course_id))
    db.commit()
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/quiz/add")
async def add_quiz(course_id: int = Form(...), title: str = Form(...), duration: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    db.add(models.Quiz(title=title, duration=duration, course_id=course_id))
    db.commit()
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/assignment/add")
async def add_assignment(course_id: int = Form(...), title: str = Form(...), max_score: float = Form(...), content: str = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    db.add(models.Assignment(title=title, max_score=max_score, content=content, course_id=course_id))
    db.commit()
    return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)

@router.post("/lesson/delete")
async def delete_lesson(lesson_id: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    item = db.query(models.Lesson).get(lesson_id)
    if item:
        course_id = item.course_id
        db.delete(item)
        db.commit()
        return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)
    return RedirectResponse(url="/teacher", status_code=302)

@router.post("/quiz/delete")
async def delete_quiz(quiz_id: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    item = db.query(models.Quiz).get(quiz_id)
    if item:
        course_id = item.course_id
        db.query(models.Question).filter(models.Question.quiz_id == quiz_id).delete()
        db.delete(item)
        db.commit()
        return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)
    return RedirectResponse(url="/teacher", status_code=302)

@router.post("/assignment/delete")
async def delete_assignment(assignment_id: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    item = db.query(models.Assignment).get(assignment_id)
    if item:
        course_id = item.course_id
        db.delete(item)
        db.commit()
        return RedirectResponse(url=f"/teacher/course/{course_id}", status_code=302)
    return RedirectResponse(url="/teacher", status_code=302)

@router.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def manage_quiz_questions(quiz_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    quiz = db.query(models.Quiz).filter(models.Quiz.quiz_id == quiz_id).first()
    if not quiz: return RedirectResponse("/teacher")
    return templates.TemplateResponse("teacher_quiz_detail.html", {"request": request, "user": user, "quiz": quiz})

@router.post("/quiz/question/add")
async def add_question(
    quiz_id: int = Form(...), content: str = Form(...), 
    option_a: str = Form(...), option_b: str = Form(...), option_c: str = Form(...), option_d: str = Form(...), 
    correct_answer: str = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)
):
    db.add(models.Question(
        quiz_id=quiz_id, content=content, question_type="single_choice",
        option_a=option_a, option_b=option_b, option_c=option_c, option_d=option_d, correct_answer=correct_answer
    ))
    db.commit()
    return RedirectResponse(url=f"/teacher/quiz/{quiz_id}", status_code=302)

@router.get("/grading", response_class=HTMLResponse)
async def grading_list(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)):
    submissions = db.query(models.Submission).order_by(models.Submission.teacher_score.asc()).all()
    return templates.TemplateResponse("teacher_grading.html", {"request": request, "user": user, "submissions": submissions})

@router.post("/grading/update")
async def update_grade(
    submission_id: int = Form(...), teacher_score: float = Form(...), feedback: str = Form(...), 
    db: Session = Depends(get_db), user: models.User = Depends(verify_teacher)
):
    sub = db.query(models.Submission).get(submission_id)
    if sub:
        sub.teacher_score = teacher_score
        sub.teacher_feedback = feedback
        sub.graded_by = "Teacher"
        db.commit()
    return RedirectResponse(url="/teacher/grading", status_code=302)