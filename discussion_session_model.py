from connection_database import Base
from sqlalchemy import Column, Integer,ForeignKey,DateTime,String
from sqlalchemy.orm import relationship
from discussion_session_topic import discussion_session_topic_table


class DiscussionSession(Base):
    __tablename__ = 'discussion_sessions'
    id = Column(Integer,primary_key=True)
    chosen_topic_id = Column(Integer,ForeignKey('discussion_topics.id'),nullable=True)
    scheduled_start_at = Column(DateTime(timezone=True),nullable=False)
    scheduled_end_at = Column(DateTime(timezone=True),nullable=False)
    actual_started_at = Column(DateTime(timezone=True))
    actual_ended_at = Column(DateTime(timezone=True))
    status = Column(String,nullable=False)
    participant_limit = Column(Integer,nullable=False)
    voting_closes_at = Column(DateTime(timezone=True),nullable=False)
    registration_closes_at = Column(DateTime(timezone=True),nullable=False)


    discussion_topic = relationship("DiscussionTopic",back_populates="discussion_sessions",
                                    foreign_keys=[chosen_topic_id]  )

    studentdiscussion_votes = relationship("StudentDiscussionVote",back_populates="discussion_session",passive_deletes=True)

    discussion_registrations = relationship("FreeDiscussionRegistration",back_populates="discussion_session",passive_deletes=True)


    offered_topics = relationship("DiscussionTopic",back_populates="offered_sessions",secondary="discussion_session_topics",passive_deletes=True)