from connection_database import Base
from sqlalchemy import Column,Integer,Table,ForeignKey


discussion_session_topic_table=Table("discussion_session_topics",Base.metadata,
                Column('discussion_topic_id',Integer,ForeignKey('discussion_topics.id',ondelete="CASCADE"),primary_key=True),
                      Column('discussion_session_id',Integer,ForeignKey('discussion_sessions.id',ondelete="CASCADE"),primary_key=True))


