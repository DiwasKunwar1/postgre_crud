from fastapi import FastAPI, HTTPException, Depends, Response, Request, Cookie, Query
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from .models import UserCreate,  LoginRequest, Product
from databse.db import SessionLocal, engine, User
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import secrets
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
import os
from .rss import scraper
from .price.price_comp import main
from typing import List
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()


SKey = os.getenv('SECRET_KEY')

# Secret key and algorithm for JWT
SECRET_KEY = SKey
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Expiry time for access tokens

# OAuth2 scheme for password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


dir_path = os.path.dirname(os.path.realpath(__file__))
i_path = os.path.join(dir_path, "templates")

index_path = os.path.join(i_path, "index.html")
home_path = os.path.join(i_path, "home.html")


# Function to verify password
def verify_password(plain_password, hashed_password):
    return bcrypt.verify(plain_password, hashed_password)


# Function to authenticate user
def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Endpoint to serve index.html
@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(index_path)


# Register user endpoint
@app.post("/register")

# def register_user(username: str, password: str, db: Session = Depends(get_db)):
def register_user(signin_request: UserCreate, db: Session = Depends(get_db)):

    username = signin_request.username
    password = signin_request.password
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = bcrypt.hash(password)
    db_user = User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"message": "User registered successfully"}


# Login endpoint
@app.post("/login")
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    username = login_request.username
    password = login_request.password

    user_from_db = db.query(User).filter(User.username == username).first()
    if not user_from_db:
        raise HTTPException(status_code=400, detail="Invalid username ")
    if not bcrypt.verify(password, user_from_db.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    # If username and password are valid, create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    # Set cookie and redirect to home page
    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key="access_token",
        value=f"{access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response


@app.get("/home", response_class=HTMLResponse)
def get_home(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return Response(content="Unauthorized", status_code=401)

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        with open(home_path, "r") as file:
            html_content = file.read()

        html_content = html_content.replace("{{ username }}", username)
        return HTMLResponse(content=html_content)

    except JWTError:
        return Response(content="Unauthorized", status_code=401)


# Users/me endpoint
@app.get("/users/me")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Update password endpoint
@app.put("/users/update_password")
def update_password(username: str, new_password: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_username: str = payload.get("sub")
        if token_username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        if token_username != username:
            raise HTTPException(status_code=403, detail="Forbidden: You can only update your own password")

        # Update password in the database
        hashed_password = bcrypt.hash(new_password)
        db.query(User).filter(User.username == username).update({"hashed_password": hashed_password})
        db.commit()

        return {"message": "Password updated successfully"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/scrape", response_model=List[dict])
async def scrape():
    try:
        the_articles = []
        for url in scraper.urls:
            articles = scraper.scrape_rss_feed(url)
            the_articles.extend(articles)
        return the_articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get('/price', response_model=List[dict])
def get_products(search_query: str = Query(..., alias="search_query")):
    results = main(search_query)
    return results

@app.get("/logout")
def logout():
    # Redirect to login page after clearing the access token cookie
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.delete_cookie("access_token")
    return response
