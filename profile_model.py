from connection_database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,String,ForeignKey


class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    first_name = Column(String,nullable=False)
    last_name = Column(String,nullable=False)
    bio = Column(String)
    avatar_url = Column(String)
    native_language = Column(String)
    learning_level = Column(String)
    user_id = Column(Integer,ForeignKey('users.id',ondelete="CASCADE"),nullable=False,unique=True)

    user=relationship("User",back_populates="profile")
