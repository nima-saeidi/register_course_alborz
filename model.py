from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# PostgreSQL Database URL
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "n1m010"
POSTGRES_DB = "course"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

# POSTGRES_USER = "postgres"
# POSTGRES_PASSWORD = "n1m010"
# POSTGRES_DB = "course"
# POSTGRES_HOST = "localhost"
# POSTGRES_PORT = "5432"

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

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

# Create tables
Base.metadata.create_all(bind=engine)
