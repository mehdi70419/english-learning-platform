from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,ForeignKey,String,UniqueConstraint


class Section(Base):
    __tablename__ = 'sections'
    __table_args__ = (
        UniqueConstraint("lesson_id", "name"),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String,nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id',ondelete='CASCADE'),nullable=False)


    lesson = relationship("Lesson",back_populates="sections")

    studysessions = relationship("StudySession",back_populates="section",passive_deletes=True)




