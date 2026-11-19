from connection_database import Base
from sqlalchemy import Column,Integer,String,ForeignKey
from sqlalchemy.orm import relationship



class Vocabulary(Base):
    __tablename__ = "vocabularies"
    id = Column(Integer,primary_key=True)
    word = Column(String,nullable=False)
    definition = Column(String,nullable=False)
    example_sentence = Column(String,nullable=False)
    part_of_speech = Column(String,nullable=False)
    pronunciation = Column(String)
    translation = Column(String)
    difficulty = Column(String)
    lesson_id = Column(Integer,ForeignKey("lessons.id",ondelete="CASCADE"),nullable=False)
    

    lesson = relationship("Lesson",back_populates="vocabularies")


