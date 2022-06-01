import os
import logging

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from crud import UserCRUD
from schemas import TokenData

logger = logging.getLogger(__name__)

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
    logger.info(msg="Start create_token")
    access_token_expires = timedelta(minutes=EXPIRE)
    response = {
        "access_token": create_access_token(
            data={"username": username, "sub": username},
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
    logger.info(msg="End create_token")
    return response


def create_access_token(data: dict, expires_delta: timedelta = None):
    logger.info(msg="Start create_access_token")
    to_encode = data.copy()
    if expires_delta:
        logger.debug(msg=f"ACCESS_TOKEN_EXPIRE_MINUTES is {expires_delta}")
        expire = datetime.utcnow() + expires_delta
    else:
        logger.debug(msg=f"ACCESS_TOKEN_EXPIRE_MINUTES don't set, set as 15 minutes as default")
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(msg="End create_access_token")
    return encoded_jwt


def get_current_user(users: UserCRUD = Depends(), token: str = Depends(oauth2_schema)):
    logger.info(msg="Start get_current_user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug(msg="Start decoding users token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error(msg="There are not username in decoded token")
            raise credentials_exception
        token_data = TokenData(username=username)
        logger.debug(msg="End decoding users token")
    except JWTError:
        logger.error(msg=f"Can't decode token: {token}")
        raise credentials_exception
    username = token_data.username
    user = users.read_by_username(username=username)
    if user is None:
        logger.error(msg=f"There are not {username} in registered users")
        raise credentials_exception
    logger.info(msg="End get_current_user")
    return user


def authenticate_user(username: str, password: str, users: UserCRUD):
    logger.info(msg="Start authenticate_user")
    user = users.read_by_username(username=username)
    if not user:
        logger.error(msg=f"Username '{username}' not found")
        raise credentials_error
    if not users.verify_password(password, user.hashed_password):
        logger.error(msg=f"Wrong password")
        raise credentials_error
    logger.info(msg="End authenticate_user")
    return user
