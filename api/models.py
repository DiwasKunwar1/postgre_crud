from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    title: str
    price: str
    image: str
    link: str
    site: str
