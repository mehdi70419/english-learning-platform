from connection_database import Base
from sqlalchemy import Column,Integer,ForeignKey,DateTime,String,UniqueConstraint
from sqlalchemy.orm import relationship




class FreeDiscussionRegistration(Base):
    __tablename__ = 'free_discussion_registrations'
    __table_args__ = (
        UniqueConstraint("discussion_session_id", "user_id"),
    )
    id = Column(Integer,primary_key=True)
    discussion_session_id = Column(Integer,ForeignKey('discussion_sessions.id',ondelete="CASCADE"),nullable=False)
    user_id = Column(Integer,ForeignKey('users.id',ondelete="CASCADE"),nullable=False)
    registered_at = Column(DateTime(timezone=True),nullable=False)
    status = Column(String,nullable=False)
    cancelled_at = Column(DateTime(timezone=True),nullable=True)

    user = relationship("User", back_populates="discussion_registrations")

    discussion_session = relationship("DiscussionSession", back_populates="discussion_registrations")