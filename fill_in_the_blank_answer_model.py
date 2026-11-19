from connection_database import Base
from sqlalchemy import Column,String,ForeignKey,Integer
from sqlalchemy.orm import relationship



class FillInTheBlankAnswer(Base):
    __tablename__ = "fill_in_the_blank_answers"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id",ondelete="CASCADE"),unique=True,nullable=False)
    accepted_answer=Column(String,nullable=False)


    question = relationship("Question",back_populates="fill_in_the_blank_answer")
