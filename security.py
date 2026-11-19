from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta,timezone
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from main import Session
from main import Depends
from connection_database import get_db
from user_model import User
from fastapi import HTTPException

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(status_code=401,detail="Could not validate credentials")

    username=payload.get("sub")
    db_user=db.query(User).filter(User.username==username).first()
    if db_user is None:
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    return db_user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role!="admin":
        raise HTTPException(status_code=403,detail="you are not an admin")
    return current_user

