from sqlalchemy.ext.asyncio import AsyncSession


from app.api.repo.user_repo import user_repo_v1
from app.api.models.users import User, GoogleUser
from app.core.exceptions import UserNotFoundError


class UserServiceV1:
    async def get_curr_user(self, email: str, session: AsyncSession) -> User:
        user: User | None = await user_repo_v1.get_user(email, session)

        if not user:
            raise UserNotFoundError(email)

        return user

    async def _get_user(self, email: str, session: AsyncSession) -> User | None:
        user: User | None = await user_repo_v1.get_unverified_user(email, session)
        return user

    async def get_google_user(
        self, user_id: str, session: AsyncSession
    ) -> GoogleUser | None:
        user: GoogleUser | None = await user_repo_v1.get_google_user(user_id, session)
        return user

    async def create_user(self, user: User | GoogleUser, session: AsyncSession):
        await user_repo_v1.add_user_to_db(user, session)

    async def update_user(self, user: User, session: AsyncSession):
        await user_repo_v1.add_user_to_db(user, session)


user_service_v1 = UserServiceV1()
