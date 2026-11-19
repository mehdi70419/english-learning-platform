from connection_database import Base
from sqlalchemy import Column,String,Integer,ForeignKey,UniqueConstraint,Boolean,DateTime
from sqlalchemy.orm import relationship


class Answer(Base):
    __tablename__ = 'answers'
    __table_args__ = (
        UniqueConstraint("user_id", "question_id"),
    )

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer,ForeignKey('questions.id',ondelete="CASCADE"),nullable=False)
    selected_answer = Column(String)
    user_id = Column(Integer,ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
    correctness = Column(Boolean,nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)
    correct_answer_snapshot = Column(String,nullable=False)


    question=relationship("Question",back_populates="answers")

    user=relationship("User",back_populates="answers")