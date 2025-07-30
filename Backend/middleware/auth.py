from fastapi  import  Request , HTTPException 
from fastapi.responses import JSONResponse
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from fastapi import status
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY','1234567890')
ALGORITHM = os.getenv('ALGORITHM','HS256')

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid token",
    headers={"WWW-Authenticate": "Bearer"}
)
async def authorise(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user_id = payload.get("user_id")
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
    