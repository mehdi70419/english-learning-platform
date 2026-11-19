from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,String,ForeignKey


class Grammar(Base):
    __tablename__ = 'grammars'
    id = Column(Integer,primary_key=True)
    title = Column(String,nullable=False)
    explanation = Column(String,nullable=False)
    examples = Column(String)
    order = Column(Integer)
    lesson_id = Column(Integer,ForeignKey('lessons.id',ondelete="CASCADE"),nullable=False)

    lesson = relationship("Lesson",back_populates="grammars")
