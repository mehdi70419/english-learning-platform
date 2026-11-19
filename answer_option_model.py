from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,ForeignKey,String,Boolean



class QuestionAnswerOption(Base):
    __tablename__ = 'answer_options'
    id = Column(Integer,primary_key=True)
    question_id = Column(Integer,ForeignKey('questions.id',ondelete="CASCADE"),nullable=False)
    option_text = Column(String,nullable=False)
    is_correct = Column(Boolean,nullable=False)



    question = relationship("Question",back_populates="answer_options")
