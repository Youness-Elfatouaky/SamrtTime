from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    login: str
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    username: str

    class Config:
        orm_mode = True
