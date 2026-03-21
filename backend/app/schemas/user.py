import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


# данные для регистрации пользователя
class UserRegister(BaseModel):
    login: str
    password: str
    password_confirm: str

    @field_validator("login")
    @classmethod
    def login_valid(cls, v: str) -> str:
        # проверка логина на длину
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Логин должен быть от 3 до 32 символов")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Логин может содержать только буквы, цифры и _")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        # проверка пароля на длину
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        # сравниваем пароль и его потверждение
        if self.password != self.password_confirm:
            raise ValueError("Пароли не совпадают")
        return self


# данные для входа
class UserLogin(BaseModel):
    login: str
    password: str


# токен для запросов
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# данные созданного пользователя (без пароля)
class UserResponse(BaseModel):
    id: str
    login: str

    class Config:
        from_attributes = True