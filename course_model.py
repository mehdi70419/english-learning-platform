from sqlalchemy.orm import relationship
from connection_database import Base
from sqlalchemy import Column,Integer,String,DateTime
from enrollment_model import enrollment_table



class Course(Base):
    __tablename__="courses"
    id=Column(Integer, primary_key=True)
    title=Column(String,nullable=False)
    description=Column(String)
    level=Column(String,nullable=False)
    created_at=Column(DateTime(timezone=True))

    lessons=relationship("Lesson",back_populates="course",passive_deletes=True,cascade="all,delete-orphan")

    users=relationship("User",back_populates="courses",secondary=enrollment_table,passive_deletes=True)