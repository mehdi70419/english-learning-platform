from sqlalchemy.orm import relationship

from connection_database import Base

from sqlalchemy import Column,INTEGER,String,Boolean

from discussion_session_topic import discussion_session_topic_table



class DiscussionTopic(Base):
    __tablename__ = 'discussion_topics'
    id = Column(INTEGER, primary_key=True)
    title = Column(String,nullable=False)
    description = Column(String,nullable=False)
    is_active = Column(Boolean,default=True,nullable=False)


    discussion_sessions = relationship("DiscussionSession",back_populates="discussion_topic",
                                       foreign_keys="DiscussionSession.chosen_topic_id")


    studentdiscussion_votes = relationship("StudentDiscussionVote",back_populates="discussion_topic",passive_deletes=True)

    offered_sessions = relationship("DiscussionSession",back_populates="offered_topics",secondary="discussion_session_topics",passive_deletes=True)