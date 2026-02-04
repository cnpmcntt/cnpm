from sqlalchemy import Column, Integer, Float, DateTime, Boolean, ForeignKey, NVARCHAR, Table
from sqlalchemy.orm import relationship
from database import Base
import datetime

parent_student_association = Table(
    'parent_student', Base.metadata,
    Column('parent_id', Integer, ForeignKey('Parents.parent_id'), primary_key=True),
    Column('student_id', Integer, ForeignKey('Students.student_id'), primary_key=True)
)

class User(Base):
    __tablename__ = "Users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    fullname = Column(NVARCHAR(100))
    email = Column(NVARCHAR(100), unique=True, index=True)
    password_hash = Column(NVARCHAR(255))
    role = Column(NVARCHAR(20))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    teacher_profile = relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent_profile = relationship("Parent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    notifications = relationship("Notification", back_populates="user")

class Teacher(Base):
    __tablename__ = "Teachers"
    
    teacher_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    teacher_code = Column(NVARCHAR(20), unique=True)
    specialization = Column(NVARCHAR(100))
    
    user = relationship("User", back_populates="teacher_profile")
    courses = relationship("Course", back_populates="teacher")

class Parent(Base):
    __tablename__ = "Parents"
    
    parent_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    phone_number = Column(NVARCHAR(20))
    
    user = relationship("User", back_populates="parent_profile")
    
    children = relationship("Student", secondary=parent_student_association, back_populates="parents")

class Student(Base):
    __tablename__ = "Students"
    
    student_id = Column(Integer, ForeignKey("Users.user_id"), primary_key=True)
    student_code = Column(NVARCHAR(20), unique=True)
    grade_level = Column(NVARCHAR(50))
    
    
    user = relationship("User", back_populates="student_profile")
    
    parents = relationship("Parent", secondary=parent_student_association, back_populates="children")
    
    payments = relationship("Payment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")
    quiz_submissions = relationship("QuizSubmission", back_populates="student")


class Course(Base):
    __tablename__ = "Course"
    
    course_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))
    description = Column(NVARCHAR)
    price = Column(Float)
    status = Column(NVARCHAR(20), default='active')
    teacher_id = Column(Integer, ForeignKey("Teachers.teacher_id"))
    
    teacher = relationship("Teacher", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="course")

class Lesson(Base):
    __tablename__ = "Lesson"
    
    lesson_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))
    content = Column(NVARCHAR)
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    
    course = relationship("Course", back_populates="lessons")

class Quiz(Base):
    __tablename__ = "Quiz"
    
    quiz_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))
    duration = Column(Integer)
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    lesson_id = Column(Integer, ForeignKey("Lesson.lesson_id"), nullable=True)
    
    course = relationship("Course", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "Question"
    
    question_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("Quiz.quiz_id"))
    content = Column(NVARCHAR)
    question_type = Column(NVARCHAR(20))
    
    option_a = Column(NVARCHAR(200))
    option_b = Column(NVARCHAR(200))
    option_c = Column(NVARCHAR(200))
    option_d = Column(NVARCHAR(200))
    correct_answer = Column(NVARCHAR(10))
    
    quiz = relationship("Quiz", back_populates="questions")

class Payment(Base):
    __tablename__ = "Payment"
    
    payment_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("Students.student_id"))
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(NVARCHAR(20))
    
    student = relationship("Student", back_populates="payments")
    course = relationship("Course", back_populates="payments")

class Notification(Base):
    __tablename__ = "Notification"
    
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    message = Column(NVARCHAR)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="notifications")

class Submission(Base):
    __tablename__ = "Submission"

    submission_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("Assignment.assignment_id"))
    student_id = Column(Integer, ForeignKey("Students.student_id"))
    answer = Column(NVARCHAR)
    ai_score = Column(Float, nullable=True)
    teacher_score = Column(Float, nullable=True)
    teacher_feedback = Column(NVARCHAR, nullable=True)
    graded_by = Column(NVARCHAR(50), nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="submissions")

class Assignment(Base):
    __tablename__ = "Assignment"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    title = Column(NVARCHAR(200))
    max_score = Column(Float)
    content = Column(NVARCHAR)
    course_id = Column(Integer, ForeignKey("Course.course_id"))
    
    course = relationship("Course", back_populates="assignments")

class QuizSubmission(Base):
    __tablename__ = "QuizSubmission"

    submission_id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("Quiz.quiz_id"))
    student_id = Column(Integer, ForeignKey("Students.student_id"))
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    quiz = relationship("Quiz")
    student = relationship("Student", back_populates="quiz_submissions")
    answers = relationship("QuizAnswer", back_populates="submission", cascade="all, delete-orphan")

class QuizAnswer(Base):
    __tablename__ = "QuizAnswer"
    
    answer_id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("QuizSubmission.submission_id"))
    question_id = Column(Integer, ForeignKey("Question.question_id"))
    selected_option = Column(NVARCHAR(10))
    is_correct = Column(Boolean)
    
    submission = relationship("QuizSubmission", back_populates="answers")
    question = relationship("Question")
