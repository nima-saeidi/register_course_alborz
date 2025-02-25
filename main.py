from fastapi import FastAPI, Depends, HTTPException,UploadFile,File,Query
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi import Form
from fastapi.responses import RedirectResponse
from uuid import uuid4
from pathlib import Path
import os
from typing import Optional
from fastapi.responses import HTMLResponse, Response
import pandas as pd
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware


# POSTGRES_USER = "postgres"
# POSTGRES_PASSWORD = "n1m010"
# POSTGRES_DB = "course"
# POSTGRES_HOST = "localhost"
# POSTGRES_PORT = "5432"


POSTGRES_USER = "alborz"
POSTGRES_PASSWORD = "n1m010"
POSTGRES_DB = "course_register"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    home_number = Column(String, nullable=True)
    mobile_number = Column(String, nullable=False)
    home_address = Column(Text, nullable=True)
    birth_date = Column(Text, nullable=True)
    profile_image_path = Column(String, nullable=True)
    info_card_image_path = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    course = relationship("Course", back_populates="students")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    students = relationship("User", back_populates="course")


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


# Pydantic Schemas
class UserCreate(BaseModel):
    name: str
    last_name: str
    home_number: str | None = None
    mobile_number: str
    home_address: str | None = None
    profile_image_path: str | None = None
    info_card_image_path: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    last_name: str
    home_number: str | None
    mobile_number: str
    home_address: str | None
    profile_image_path: str | None
    info_card_image_path: str | None
    course_id: int | None

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    name: str
    description: str | None = None


class CourseResponse(BaseModel):
    id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True


# FastAPI Application
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (replace with specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/courses")
def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()  # Get all courses
    if not courses:
        raise HTTPException(status_code=404, detail="No courses found")

    # Return a list of dictionaries with both id and name
    course_list = [{"id": course.id, "name": course.name} for course in courses]

    return {"courses": course_list}


Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserCreate(BaseModel):
    name: str
    last_name: str
    mobile_number: str
    birth_date: str
    home_number: str | None = None
    home_address: str | None = None
    course_id: int | None = None


@app.post("/register/")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if course_id is provided and exists
    # if user_data.course_id:
    #     course = db.query(Course).filter(Course.id == user_data.course_id).first()
    #     if not course:
    #         raise HTTPException(status_code=400, detail="Invalid course_id: Course does not exist")

    user = User(
        name=user_data.name,
        last_name=user_data.last_name,
        mobile_number=user_data.mobile_number,
        birth_date=user_data.birth_date,
        home_number=user_data.home_number,
        home_address=user_data.home_address,
        course_id=user_data.course_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "user_id": user.id}


import shutil
import os

@app.post("/upload-profile/{user_id}")
def upload_profile_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = os.path.join(UPLOAD_DIR, f"profile_{user_id}.jpg")
    print(f"Saving file to: {file_path}")  # Debugging output

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user.profile_image_path = file_path
        db.commit()
        return {"message": "Profile image uploaded successfully", "file_path": file_path}
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/upload-info-card/{user_id}")
def upload_info_card_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = os.path.join(UPLOAD_DIR, f"info_card_{user_id}.jpg")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.info_card_image_path = file_path
    db.commit()
    return {"message": "Info card image uploaded successfully"}


class AdminRegister(BaseModel):
    username: str
    password: str


class AdminLogin(BaseModel):
    username: str
    password: str


# Admin endpoints
@app.post("/admin/register/")
def register_admin(admin: AdminRegister, db: Session = Depends(get_db)):
    db_admin = db.query(Admin).filter(Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    hashed_password = pwd_context.hash(admin.password)
    new_admin = Admin(username=admin.username, password_hash=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"msg": "Admin registered successfully"}


@app.get("/admin/login/", response_class=HTMLResponse)
def get_admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login/")
def login_admin(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not pwd_context.verify(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return RedirectResponse(url="/admin/users/", status_code=303)



@app.get("/admin/users/", response_class=HTMLResponse)
def get_all_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
def get_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_detail.html", {"request": request, "user": user})


@app.get("/admin/courses/{course_id}/students", response_class=HTMLResponse)
def get_students_in_course(
        course_id: int,
        request: Request,
        db: Session = Depends(get_db),
        sort_by: Optional[str] = Query(None,
                                       description="Sort students by a specific field (name, last_name, mobile_number)")
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students_query = db.query(User).filter(User.course_id == course_id)

    if sort_by in ["name", "last_name", "mobile_number"]:
        students_query = students_query.order_by(getattr(User, sort_by))

    students = students_query.all()

    return templates.TemplateResponse("students_in_course.html", {
        "request": request,
        "course": course,
        "students": students,
        "sort_by": sort_by
    })


@app.get("/admin/courses/{course_id}/students/export", response_class=Response)
def export_students_to_excel(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students = db.query(User).filter(User.course_id == course_id).all()

    data = [
        {"ID": s.id, "Name": s.name, "Last Name": s.last_name, "Mobile Number": s.mobile_number,
         "Home Address": s.home_address, "Course": s.course.name}
        for s in students
    ]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Students")

    output.seek(0)

    headers = {
        "Content-Disposition": f"attachment; filename=students_in_{course.name}.xlsx",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    return Response(content=output.getvalue(), headers=headers)

@app.post("/admin/courses/")
def create_course(name: str = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.name == name).first()
    if db_course:
        raise HTTPException(status_code=400, detail="Course already exists")
    db_course = Course(name=name, description=description)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return RedirectResponse(url="/admin/courses/add", status_code=303)


@app.get("/admin/courses/add", response_class=HTMLResponse)
def render_add_course_page(request: Request):
    return templates.TemplateResponse("add_course.html", {"request": request})


# Route to list all courses
@app.get("/admin/courses", response_class=HTMLResponse)
def list_courses(request: Request, db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    return templates.TemplateResponse("courses_list.html", {"request": request, "courses": courses})

# Route to edit a course
@app.get("/admin/courses/edit/{course_id}", response_class=HTMLResponse)
def edit_course_page(request: Request, course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return templates.TemplateResponse("edit_course.html", {"request": request, "course": course})

@app.post("/admin/courses/edit/{course_id}")
def edit_course(course_id: int, name: str = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.name = name
    course.description = description
    db.commit()
    db.refresh(course)
    return RedirectResponse(url="/admin/courses", status_code=303)

# Route to delete a course
@app.post("/admin/courses/delete/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return RedirectResponse(url="/admin/courses", status_code=303)



Base.metadata.create_all(bind=engine)
