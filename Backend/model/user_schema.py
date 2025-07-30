from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str
class UserResponse(BaseModel):
    email: EmailStr
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
