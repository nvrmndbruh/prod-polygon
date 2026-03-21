import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


# регистрация нового пользователя
class UserRegister(BaseModel):
    login: str
    password: str
    password_confirm: str

    # валидация логина
    @field_validator("login")
    @classmethod
    def login_valid(cls, v: str) -> str:
        
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Длина логина должна быть от 3 до 32 символов")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Логин может содержать только буквы, цифры и символ подчеркивания")
        return v

    # валидация пароля
    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Длина пароля должна быть не менее 6 символов")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        if self.password != self.password_confirm:
            raise ValueError("Пароли не совпадают")
        return self


# вход в систему
class UserLogin(BaseModel):
    login: str
    password: str


# токен
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ответ при регистрации пользователя (без пароля)
class UserResponse(BaseModel):
    id: str
    login: str

    class Config:
        from_attributes = True