from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,ForeignKey,DateTime,UniqueConstraint


class StudentDiscussionVote(Base):
    __tablename__ = 'student_discussion_votes'
    __table_args__ = (
        UniqueConstraint("discussion_session_id", "user_id"),
    )
    id = Column(Integer,primary_key=True)
    discussion_session_id = Column(Integer,ForeignKey("discussion_sessions.id",ondelete="CASCADE"),nullable=False)
    discussion_topic_id = Column(Integer,ForeignKey("discussion_topics.id",ondelete="CASCADE"),nullable=False)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)


    user = relationship("User",back_populates="studentdiscussion_votes")

    discussion_session = relationship("DiscussionSession",back_populates="studentdiscussion_votes")

    discussion_topic = relationship("DiscussionTopic",back_populates="studentdiscussion_votes")
