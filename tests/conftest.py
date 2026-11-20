from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from connection_database import Base
from main import app
from connection_database import get_db as original_get_db
import pytest
from fastapi.testclient import TestClient

import os
from dotenv import load_dotenv
load_dotenv()



@pytest.fixture
def client():
    return TestClient(app)


TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured")



engine = create_engine(TEST_DATABASE_URL)

Base.metadata.create_all(bind=engine)

Sessionlocal = sessionmaker(bind=engine)

def test_get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[original_get_db] = test_get_db

