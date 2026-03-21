from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.db_session import get_db
from app.db.models import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# регистраци€ нового пользовател€
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    –егистраци€ нового пользовател€.
    ѕровер€ет уникальность логина, хэширует пароль и сохран€ет пользовател€.
    ¬озвращает данные созданного пользовател€ без парол€.
    """
    result = await db.execute(select(User).where(User.login == data.login))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ѕользователь с таким логином уже существует",
        )

    user = User(
        login=data.login,
        password_hash=get_password_hash(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(id=str(user.id), login=user.login)


# вход в систему
@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    ¬ход в систему.
    ѕровер€ет логин и пароль, возвращает JWT-токен.
    Ќамеренно возвращаем одинаковое сообщение при неверном логине
    и неверном пароле Ч чтобы не давать подсказок злоумышленнику.
    """
    result = await db.execute(select(User).where(User.login == data.login))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ќеверный логин или пароль",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token)