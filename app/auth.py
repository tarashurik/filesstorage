import os
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from crud import UserCRUD
from schemas import TokenData

load_dotenv()

ALGORITHM = os.environ.get('PASSWORD_HASH_ALGORITHM')
SECRET_KEY = os.environ.get('PASSWORD_HASH_SECRET_KEY')
EXPIRE = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES'))

oauth2_schema = OAuth2PasswordBearer(tokenUrl='/users/token')

credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_token(username: str) -> dict:
    access_token_expires = timedelta(minutes=EXPIRE)
    return {
        "access_token": create_access_token(
            data={"username": username, "sub": username},
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(users: UserCRUD = Depends(), token: str = Depends(oauth2_schema)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = users.read_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(username: str, password: str, users: UserCRUD):
    user = users.read_by_username(username=username)
    if not user:
        return False
    if not users.verify_password(password, user.hashed_password):
        return False
    return user
