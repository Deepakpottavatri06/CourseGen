from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from typing import Dict
from model.db_connect import db
from model.user_schema import User, UserResponse, UserLogin
#models: User, UserCreate, UserResponse



load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', '1234567890')
ALGORITHM = os.getenv('ALGORITHM', 'HS256') 


pwd_context = CryptContext(schemes=['bcrypt'])



# Middleware-like Dependency for Auth


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app = APIRouter()


async def authenticate_user(email: str, password: str):
    user = await db['users'].find_one({"email": email})
    if not user:
        return None
    return user


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=6)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/register", response_model=UserResponse)
async def register(user: User):
    try:
        if await authenticate_user(user.email, user.password):
            raise HTTPException(status_code=400, detail="Email already registered")
    
        hashed = hash_password(user.password)
        await db['users'].insert_one({
            "email": user.email,
            "name": user.name,
            "password": hashed
        })
        return JSONResponse(content=UserResponse(email=user.email, name=user.name).model_dump(), status_code=status.HTTP_201_CREATED)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(form: UserLogin):
    try:
        user = await authenticate_user(form.email, form.password)
        if not user or not verify_password(form.password, user['password']):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        access_token = create_access_token(data={"user_id": str(user['_id']), "email": user['email']})
        return JSONResponse(content={"access_token": access_token, "token_type": "bearer"}, status_code=status.HTTP_200_OK)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")