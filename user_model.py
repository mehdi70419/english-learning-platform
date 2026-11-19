from connection_database import Base
from sqlalchemy import Column,Integer,String,DateTime
from sqlalchemy.orm import relationship
from enrollment_model import enrollment_table



class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True)
    username = Column(String,unique=True,nullable=False)
    email = Column(String,unique=True,nullable=False)
    hashed_password = Column(String,nullable=False)
    role=Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True),nullable=False)
    last_activity_at = Column(DateTime(timezone=True),nullable=True)

    profile=relationship("Profile",back_populates="user",uselist=False,passive_deletes=True)

    courses=relationship("Course",back_populates="users",secondary=enrollment_table,passive_deletes=True)


    answers=relationship("Answer",back_populates="user",passive_deletes=True)


    study_sessions=relationship("StudySession",back_populates="user",passive_deletes=True)


    studentdiscussion_votes = relationship("StudentDiscussionVote",back_populates="user",passive_deletes=True)

    discussion_registrations = relationship("FreeDiscussionRegistration",back_populates="user",passive_deletes=True)
