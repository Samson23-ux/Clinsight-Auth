from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.api.models.users import User, GoogleUser


class UserRepoV1:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        stmt = select(User).where(User.email == email, User.is_active.is_(True))

        res = await session.execute(stmt)
        user: User | None = res.scalar()

        return user

    async def get_google_user(
        self, user_id: str, session: AsyncSession
    ) -> GoogleUser | None:
        stmt = select(GoogleUser).where(GoogleUser.user_id == user_id)

        res = await session.execute(stmt)
        user: GoogleUser | None = res.scalar()

        return user

    async def add_user_to_db(self, user: User | GoogleUser, session: AsyncSession):
        """create and update user"""
        session.add(user)
        await session.flush()
        await session.refresh(user)


user_repo_v1 = UserRepoV1()
