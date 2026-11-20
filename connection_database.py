from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base


import os
from dotenv import load_dotenv
load_dotenv()


Base = declarative_base()

db_url = os.getenv('db_url')
if not db_url:
    raise RuntimeError("db_url is not configured")


engine = create_engine(db_url)

Sessionlocal = sessionmaker(bind=engine)

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

