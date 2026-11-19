from sqlalchemy.orm import relationship
from connection_database import Base
from sqlalchemy import Column,Integer,String,ForeignKey

class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(Integer,primary_key=True)
    title = Column(String,nullable=False)
    description = Column(String,nullable=False)
    content = Column(String,nullable=False)
    order = Column(Integer,nullable=False)
    course_id = Column(Integer,ForeignKey('courses.id',ondelete="CASCADE"),nullable=False)


    course=relationship("Course",back_populates="lessons")

    vocabularies = relationship("Vocabulary",back_populates="lesson",passive_deletes=True,cascade="all,delete-orphan")

    exercises = relationship("Exercise",back_populates="lesson",passive_deletes=True,cascade="all,delete-orphan")


    study_sessions = relationship("StudySession", back_populates="lesson", passive_deletes=True)

    sections = relationship("Section",back_populates="lesson",passive_deletes=True,cascade="all,delete-orphan")


    grammars = relationship("Grammar",back_populates="lesson",passive_deletes=True,cascade="all,delete-orphan")