from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    is_verified = Column(Boolean, default=False)
    # 👇 NEW: Stores the unique code sent to email
    verification_token = Column(String, nullable=True)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    price = Column(Float)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    
    contents = relationship("Content", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")

class Content(Base):
    __tablename__ = "contents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    file_url = Column(String)
    content_type = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="contents")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    options = Column(String)
    correct_answer = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="quizzes")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    transaction_id = Column(String)
    
    completed_videos = Column(String, default="")
    completed_quizzes = Column(String, default="")
    
    course = relationship("Course", back_populates="enrollments")
    student = relationship("User")