from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,String,ForeignKey,DateTime

class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer,primary_key=True)
    title = Column(String,nullable=False)
    instructions = Column(String,nullable=False)
    exercise_type = Column(String,nullable=False)
    difficulty = Column(String,nullable=False)
    order = Column(Integer,nullable=False)
    lesson_id = Column(Integer,ForeignKey('lessons.id',ondelete="CASCADE"),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)

    lesson = relationship("Lesson",back_populates="exercises")

    questions = relationship("Question",back_populates="exercise",passive_deletes=True,cascade="all,delete-orphan")

