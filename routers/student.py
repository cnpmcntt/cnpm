from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dependencies import get_db, get_current_user
import models
import datetime
import traceback

from database import SessionLocal 

from services.ai_grader import grade_submission_with_ai

router = APIRouter(prefix="/student", tags=["Student"])
templates = Jinja2Templates(directory="templates")

def verify_student(user: models.User = Depends(get_current_user)):
    if not user or user.role != "student":
        raise HTTPException(status_code=403, detail="Chỉ dành cho Học sinh.")
    return user

def process_ai_grading(submission_id: int, question: str, answer: str):
    print(f"[Background] Đang chấm AI cho bài nộp #{submission_id}...")
    
    try:
        ai_result = grade_submission_with_ai(question, answer)
    except Exception as e:
        print(f"Lỗi khi gọi AI: {e}")
        return

    db = SessionLocal()
    try:
        submission = db.query(models.Submission).filter(models.Submission.submission_id == submission_id).first()
        if submission:
            submission.ai_score = ai_result['score']
            submission.ai_feedback = ai_result['feedback']
            
            submission.teacher_score = ai_result['score']
            submission.teacher_feedback = ai_result['feedback']
            
            db.commit()
            print(f"[Background] Đã lưu điểm bài #{submission_id}: {ai_result['score']}")
        else:
            print(f"Không tìm thấy bài nộp #{submission_id} trong DB")
            
    except Exception as e:
        print(f"Lỗi Database trong Background Task: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    student = user.student_profile
    if not student: return "Lỗi: Tài khoản chưa có hồ sơ học sinh (student_profile)."

    my_courses = db.query(models.Course).join(models.Payment).filter(
        models.Payment.student_id == student.student_id,
        models.Payment.status == 'paid'
    ).all()
    
    unread_notifs = db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False
    ).count()

    return templates.TemplateResponse("student_dashboard.html", {
        "request": request, "user": user, 
        "courses": my_courses, 
        "unread_notifs": unread_notifs
    })

@router.get("/courses", response_class=HTMLResponse)
async def course_catalog(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    all_courses = db.query(models.Course).filter(models.Course.status == 'active').all()
    
    student = user.student_profile
    if not student: return RedirectResponse("/student")

    paid_courses = db.query(models.Payment.course_id).filter(
        models.Payment.student_id == student.student_id,
        models.Payment.status == 'paid'
    ).all()
    paid_ids = [c[0] for c in paid_courses]

    return templates.TemplateResponse("student_courses.html", {
        "request": request, "user": user, 
        "courses": all_courses,
        "paid_ids": paid_ids
    })

@router.post("/course/buy")
async def buy_course(course_id: int = Form(...), db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    student = user.student_profile
    if not student: return RedirectResponse("/student")

    course = db.query(models.Course).get(course_id)
    
    if course:
        existing = db.query(models.Payment).filter(
            models.Payment.student_id == student.student_id, 
            models.Payment.course_id == course_id
        ).first()
        
        if not existing:
            new_payment = models.Payment(
                student_id=student.student_id,
                course_id=course_id,
                amount=course.price,
                status='paid',
                payment_date=datetime.datetime.utcnow()
            )
            db.add(new_payment)
            db.commit()
    
    return RedirectResponse(url="/student?msg=bought_success", status_code=302)

@router.get("/learn/{course_id}", response_class=HTMLResponse)
async def learn_course(course_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    student = user.student_profile
    if not student: return RedirectResponse("/student")
    
    payment = db.query(models.Payment).filter(
        models.Payment.student_id == student.student_id,
        models.Payment.course_id == course_id,
        models.Payment.status == 'paid'
    ).first()
    
    if not payment:
        return RedirectResponse("/student/courses?msg=need_buy")

    course = db.query(models.Course).get(course_id)
    return templates.TemplateResponse("student_learn.html", {
        "request": request, "user": user, "course": course
    })

@router.get("/quiz/take/{quiz_id}", response_class=HTMLResponse)
async def take_quiz(quiz_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    quiz = db.query(models.Quiz).get(quiz_id)
    if not quiz: return RedirectResponse("/student")
    
    return templates.TemplateResponse("student_take_quiz.html", {
        "request": request, "user": user, "quiz": quiz
    })

@router.post("/quiz/submit/{quiz_id}")
async def submit_quiz(
    quiz_id: int, 
    request: Request, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(verify_student)
):
    try:
        form_data = await request.form()
        quiz = db.query(models.Quiz).get(quiz_id)
        student = user.student_profile
        
        if not quiz or not student: return RedirectResponse("/student")

        new_submission = models.QuizSubmission(
            quiz_id=quiz_id,
            student_id=student.student_id,
            score=0,
            submitted_at=datetime.datetime.utcnow()
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)

        correct_count = 0
        total_questions = len(quiz.questions)

        for q in quiz.questions:
            selected_option = form_data.get(f"q_{q.question_id}")
            
            is_correct = False
            if selected_option and selected_option == q.correct_answer:
                is_correct = True
                correct_count += 1
            
            db.add(models.QuizAnswer(
                submission_id=new_submission.submission_id,
                question_id=q.question_id,
                selected_option=selected_option,
                is_correct=is_correct
            ))

        final_score = 0
        if total_questions > 0:
            final_score = round((correct_count / total_questions) * 10, 2)
        
        new_submission.score = final_score
        db.commit()
        
        return RedirectResponse(url=f"/student/quiz/result/{new_submission.submission_id}?msg=success", status_code=302)

    except Exception as e:
        print(f"LỖI KHI NỘP QUIZ: {e}")
        return f"Lỗi Server: {e}"

@router.get("/quiz/result/{submission_id}", response_class=HTMLResponse)
async def quiz_result(submission_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    submission = db.query(models.QuizSubmission).filter(models.QuizSubmission.submission_id == submission_id).first()
    if not submission: return RedirectResponse("/student")

    return templates.TemplateResponse("student_quiz_result.html", {
        "request": request, "user": user, "submission": submission
    })

@router.get("/assignment/{assign_id}", response_class=HTMLResponse)
async def view_assignment(assign_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    assign = db.query(models.Assignment).get(assign_id)
    student = user.student_profile
    if not student: return RedirectResponse("/student")
    
    submission = db.query(models.Submission).filter(
        models.Submission.assignment_id == assign_id,
        models.Submission.student_id == student.student_id
    ).first()

    return templates.TemplateResponse("student_do_assignment.html", {
        "request": request, "user": user, "assign": assign, "submission": submission
    })

@router.post("/assignment/submit")
async def submit_assignment(
    background_tasks: BackgroundTasks,
    assignment_id: int = Form(...), 
    answer: str = Form(...), 
    db: Session = Depends(get_db), 
    user: models.User = Depends(verify_student)
):
    student = user.student_profile
    if not student: return RedirectResponse("/student")

    assignment = db.query(models.Assignment).get(assignment_id)
    if not assignment:
        return RedirectResponse(url="/student?error=assignment_not_found", status_code=302)

    submission = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_id == student.student_id
    ).first()
    
    if submission:
        submission.answer = answer
        submission.submitted_at = datetime.datetime.utcnow()
        submission.ai_score = None 
        submission.teacher_score = None
    else:
        submission = models.Submission(
            assignment_id=assignment_id,
            student_id=student.student_id,
            answer=answer,
            submitted_at=datetime.datetime.utcnow()
        )
        db.add(submission)
    
    db.commit()
    db.refresh(submission)

    question_text = getattr(assignment, 'description', getattr(assignment, 'content', getattr(assignment, 'title', 'Không có đề bài')))

    background_tasks.add_task(
        process_ai_grading, 
        submission.submission_id, 
        question_text,
        answer
    )
    
    return RedirectResponse(url=f"/student/assignment/{assignment_id}?msg=submitted_ai_processing", status_code=302)

@router.get("/notifications", response_class=HTMLResponse)
async def student_notifications(request: Request, db: Session = Depends(get_db), user: models.User = Depends(verify_student)):
    notifs = db.query(models.Notification).filter(models.Notification.user_id == user.user_id).order_by(desc(models.Notification.created_at)).all()
    
    for n in notifs:
        if not n.is_read: n.is_read = True
    db.commit()

    return templates.TemplateResponse("student_notifications.html", {
        "request": request, "user": user, "notifications": notifs
    })