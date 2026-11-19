from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,String,ForeignKey,DateTime


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    question_text = Column(String,nullable=False)
    question_type = Column(String,nullable=False)
    order = Column(Integer,nullable=False)
    points = Column(Integer,nullable=False)
    exercise_id = Column(Integer,ForeignKey("exercises.id",ondelete="CASCADE"),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)


    exercise = relationship("Exercise",back_populates="questions")

    answers = relationship("Answer",back_populates="question",passive_deletes=True)

    answer_options = relationship("QuestionAnswerOption",back_populates="question",passive_deletes=True)


    fill_in_the_blank_answer=relationship("FillInTheBlankAnswer",back_populates="question",uselist=False,passive_deletes=True)