import pytest
from datetime import timedelta
from pydantic import ValidationError

# Замени пути импортов на актуальные для твоей структуры проекта
from app.user import UserRegister, UserLogin
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


# === ТЕСТЫ БЕЗОПАСНОСТИ (JWT и Пароли) ===

def test_password_hashing():
    """Проверка, что хэширование работает и пароль корректно валидируется."""
    plain_password = "my_strong_password123"
    hashed_password = get_password_hash(plain_password)
    
    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False


def test_create_and_decode_access_token():
    """Проверка генерации и успешного декодирования JWT токена."""
    data = {"sub": "test_user"}
    token = create_access_token(data=data)
    
    decoded_data = decode_access_token(token)
    assert decoded_data is not None
    assert decoded_data.get("sub") == "test_user"
    assert "exp" in decoded_data  # Проверяем, что срок действия установлен


def test_decode_invalid_token():
    """Проверка, что система корректно отбраковывает невалидные токены."""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI.invalid.signature"
    decoded_data = decode_access_token(invalid_token)
    assert decoded_data is None


# === ТЕСТЫ ВАЛИДАЦИИ ПОЛЬЗОВАТЕЛЯ (Pydantic) ===

def test_user_register_valid():
    """Успешная регистрация с корректными данными."""
    user = UserRegister(
        login="valid_login_123",
        password="strongpassword",
        password_confirm="strongpassword"
    )
    assert user.login == "valid_login_123"


def test_user_register_invalid_login_length():
    """Логин слишком короткий или слишком длинный."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(login="ab", password="password123", password_confirm="password123")
    assert "Длина логина должна быть от 3 до 32 символов" in str(exc_info.value)


def test_user_register_invalid_login_chars():
    """Логин содержит недопустимые символы."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(login="user@name!", password="password123", password_confirm="password123")
    assert "Логин может содержать только буквы, цифры и символ подчеркивания" in str(exc_info.value)


def test_user_register_password_too_short():
    """Пароль короче 6 символов."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(login="user_name", password="123", password_confirm="123")
    assert "Длина пароля должна быть не менее 6 символов" in str(exc_info.value)


def test_user_register_passwords_do_not_match():
    """Пароль и подтверждение пароля не совпадают."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(login="user_name", password="password123", password_confirm="password321")
    assert "Пароли не совпадают" in str(exc_info.value)