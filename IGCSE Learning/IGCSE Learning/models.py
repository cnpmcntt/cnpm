from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import NVARCHAR 
from database import Base
import datetime

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, index=True)
    fullname = Column(NVARCHAR(100))  
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20)) 

    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    
    notifications = relationship("Notification", back_populates="user")

class Student(Base):
    __tablename__ = "Students"

    student_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    student_code = Column(String(20), unique=True)
    grade_level = Column(NVARCHAR(50))

    user = relationship("User", back_populates="student_profile")
    payments = relationship("Payment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")

class Teacher(Base):
    __tablename__ = "Teachers"

    teacher_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    teacher_code = Column(String(20), unique=True)
    specialization = Column(NVARCHAR(100)) 

    user = relationship("User", back_populates="teacher_profile")
    courses = relationship("Course", back_populates="teacher")

class Course(Base):
    __tablename__ = "Course"

    course_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))        
    description = Column(NVARCHAR(None)) 
    price = Column(Float)
    status = Column(String(20), default='active')
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"))

    teacher = relationship("Teacher", back_populates="courses")
    
    lessons = relationship("Lesson", back_populates="course")
    quizzes = relationship("Quiz", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    payments = relationship("Payment", back_populates="course")

class Lesson(Base):
    __tablename__ = "Lesson"
    
    lesson_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))        
    content = Column(NVARCHAR(None))     
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    
    course = relationship("Course", back_populates="lessons")
    quizzes = relationship("Quiz", back_populates="lesson")

class Quiz(Base):
    __tablename__ = "Quiz"
    
    quiz_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))       
    duration = Column(Integer)
    
    course_id = Column(Integer, ForeignKey("Course.course_id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("Lesson.lesson_id"), nullable=True)
    
    course = relationship("Course", back_populates="quizzes")
    lesson = relationship("Lesson", back_populates="quizzes")
    
    questions = relationship("Question", back_populates="quiz")

class Question(Base):
    __tablename__ = "Question"
    question_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("Quiz.quiz_id"))
    content = Column(NVARCHAR(None))     
    question_type = Column(String(20))
    
    option_a = Column(NVARCHAR(200))
    option_b = Column(NVARCHAR(200))
    option_c = Column(NVARCHAR(200))
    option_d = Column(NVARCHAR(200))
    correct_answer = Column(String(10))
    
    quiz = relationship("Quiz", back_populates="questions")

class Assignment(Base):
    __tablename__ = "Assignment"
    assignment_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))        
    max_score = Column(Float)
    
    content = Column(NVARCHAR(None)) 
    
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    __tablename__ = "Submission"
    submission_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("Assignment.assignment_id"))
    student_id = Column(Integer, ForeignKey("Students.student_id"))
    
    answer = Column(NVARCHAR(None))
    
    ai_score = Column(Float, nullable=True)
    teacher_score = Column(Float, nullable=True)
    teacher_feedback = Column(NVARCHAR(None))
    graded_by = Column(String(20), nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")

class QuizSubmission(Base):
    __tablename__ = "QuizSubmission"
    submission_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("Quiz.quiz_id"))
    student_id = Column(Integer, ForeignKey("Users.user_id"))
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    quiz = relationship("Quiz")
    student = relationship("User")

class Payment(Base):
    __tablename__ = "Payment"
    payment_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("Students.student_id"))
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20))

    student = relationship("Student", back_populates="payments")
    course = relationship("Course", back_populates="payments")

class Notification(Base):
    __tablename__ = "Notification"
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    message = Column(NVARCHAR(300)) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")