from connection_database import Base
from sqlalchemy import Column, Integer,Table,ForeignKey

enrollment_table=Table(
    'enrollment',Base.metadata,
           Column('user_id',Integer,ForeignKey('users.id',ondelete="CASCADE"),primary_key=True),
           Column('course_id',Integer,ForeignKey('courses.id',ondelete="CASCADE"),primary_key=True))