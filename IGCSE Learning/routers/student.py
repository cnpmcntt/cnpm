from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
import models
from services.ai_grader import grade_submission 

router = APIRouter(prefix="/student", tags=["Student"])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "student": return RedirectResponse("/login")
    
    all_courses = db.query(models.Course).all()
    
    purchased_ids = []
    if user.student_profile: 
        purchased = db.query(models.Payment).filter(models.Payment.student_id == user.user_id).all()
        purchased_ids = [p.course_id for p in purchased]
    
    return templates.TemplateResponse("dashboard_student.html", {
        "request": request, "user": user, "all_courses": all_courses, "purchased_ids": purchased_ids
    })

@router.post("/buy")
async def buy_course(course_id: int = Form(...), amount: float = Form(...), user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(models.Payment).filter(models.Payment.student_id == user.user_id, models.Payment.course_id == course_id).first()
    if existing:
        return RedirectResponse(url="/student", status_code=302)

    payment = models.Payment(student_id=user.user_id, course_id=course_id, amount=amount, status="completed")
    db.add(payment)
    db.commit()
    return RedirectResponse(url="/student", status_code=302)

@router.get("/course/{course_id}", response_class=HTMLResponse)
async def learn_course(course_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user: return RedirectResponse("/login")

    is_enrolled = db.query(models.Payment).filter(
        models.Payment.student_id == user.user_id, 
        models.Payment.course_id == course_id
    ).first()
    
    if not is_enrolled:
        return HTMLResponse("<h1>Bạn chưa mua khóa học này! <a href='/student'>Quay lại</a></h1>", status_code=403)
    
    course = db.query(models.Course).filter(models.Course.course_id == course_id).first()
    
    submissions = db.query(models.Submission).join(models.Assignment).filter(
        models.Submission.student_id == user.user_id,
        models.Assignment.course_id == course_id
    ).all()
    
    submission_map = {sub.assignment_id: sub for sub in submissions}

    return templates.TemplateResponse("student_course_detail.html", {
        "request": request, 
        "user": user, 
        "course": course,
        "submission_map": submission_map 
    })


@router.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def take_quiz(quiz_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user: return RedirectResponse("/login")
    
    quiz = db.query(models.Quiz).filter(models.Quiz.quiz_id == quiz_id).first()
    if not quiz:
        return HTMLResponse("<h1>Không tìm thấy bài kiểm tra</h1>", status_code=404)
        
    return templates.TemplateResponse("student_take_quiz.html", {
        "request": request, "user": user, "quiz": quiz
    })

@router.post("/submit_quiz")
async def submit_quiz(
    request: Request, 
    quiz_id: int = Form(...), 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(models.Quiz).filter(models.Quiz.quiz_id == quiz_id).first()
    questions = quiz.questions
    
    total_questions = len(questions)
    if total_questions == 0:
        return HTMLResponse("Bài thi này chưa có câu hỏi.", status_code=400)

    form_data = await request.form()
    correct_count = 0
    
    for q in questions:
        user_answer = form_data.get(f"question_{q.question_id}")
        if user_answer and user_answer == q.correct_answer:
            correct_count += 1
            
    final_score = round((correct_count / total_questions) * 10, 2)
    
    submission = models.QuizSubmission(
        quiz_id=quiz_id,
        student_id=user.user_id,
        score=final_score
    )
    db.add(submission)
    db.commit()
    
    return templates.TemplateResponse("student_quiz_result.html", {
        "request": request, 
        "quiz": quiz, 
        "score": final_score, 
        "correct_count": correct_count, 
        "total": total_questions
    })


@router.post("/submit_assignment")
async def submit_assignment(
    course_id: int = Form(...),
    assignment_id: int = Form(...),
    answer: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    assignment = db.query(models.Assignment).filter(models.Assignment.assignment_id == assignment_id).first()
    if not assignment:
        return HTMLResponse("Không tìm thấy bài tập", status_code=404)

    question_content = assignment.content if assignment.content else assignment.title
    
    ai_score, ai_feedback = grade_submission(
        assignment_content=question_content,
        student_answer=answer,
        max_score=assignment.max_score
    )

    submission = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_id == user.user_id
    ).first()

    if submission:
        submission.answer = answer
        submission.ai_score = ai_score          
        submission.teacher_feedback = f"[AI Chấm]: {ai_feedback}"
        submission.graded_by = "AI_Bot"
        submission.teacher_score = ai_score 
    else:
        new_submission = models.Submission(
            assignment_id=assignment_id,
            student_id=user.user_id,
            answer=answer,
            ai_score=ai_score,                 
            teacher_feedback=f"[AI Chấm]: {ai_feedback}", 
            graded_by="AI_Bot",
            teacher_score=ai_score              
        )
        db.add(new_submission)

    db.commit()

    return RedirectResponse(url=f"/student/course/{course_id}", status_code=302)

@router.get("", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.role != "student": return RedirectResponse("/login")
    
    all_courses = db.query(models.Course).all()
    
    purchased_ids = []
    if user.student_profile: 
        purchased = db.query(models.Payment).filter(models.Payment.student_id == user.user_id).all()
        purchased_ids = [p.course_id for p in purchased]

    unread_count = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False
    ).count()
    
    return templates.TemplateResponse("dashboard_student.html", {
        "request": request, 
        "user": user, 
        "all_courses": all_courses, 
        "purchased_ids": purchased_ids,
        "unread_count": unread_count
    })

@router.get("/notifications", response_class=HTMLResponse)
async def view_notifications(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user: return RedirectResponse("/login")

    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id
    ).order_by(models.Notification.created_at.desc()).all()

    for notif in notifications:
        if not notif.is_read:
            notif.is_read = True
    db.commit()

    return templates.TemplateResponse("student_notifications.html", {
        "request": request, 
        "user": user, 
        "notifications": notifications
    })