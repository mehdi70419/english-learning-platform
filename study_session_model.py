from connection_database import Base
from sqlalchemy import Column,Integer,ForeignKey,DateTime,Float,String
from sqlalchemy.orm import relationship



class StudySession(Base):
    __tablename__ = 'study_sessions'
    id = Column(Integer,primary_key=True)
    lesson_id = Column(Integer,ForeignKey('lessons.id',ondelete="CASCADE"),nullable=False)
    user_id = Column(Integer,ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
    started_at = Column(DateTime(timezone=True),nullable=False)
    ended_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    section_id = Column(Integer,ForeignKey('sections.id',ondelete="CASCADE"))




    user=relationship("User",back_populates="study_sessions")

    lesson=relationship("Lesson",back_populates="study_sessions")

    section = relationship("Section",back_populates="studysessions")



