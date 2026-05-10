import enum
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, timezone


class TokenStatus(str, enum.Enum):
    VALID: str = "valid"
    REVOKED: str = "revoked"
    USED: str = "used"


class TokenDataV1(BaseModel):
    email: str


class TokenV1(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    id: UUID
    token: str
    user_email: UUID
    status: TokenStatus
    expires_at: datetime
    created_at: datetime = datetime.now(timezone.utc)
