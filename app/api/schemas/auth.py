from pydantic import BaseModel


class TokenDataV1(BaseModel):
    email: str


class TokenV1(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EmailVerifyV1(BaseModel):
    email: str
    otp_token: str


class ResendOtpV1(BaseModel):
    email: str


class EmailLoginV1(BaseModel):
    email: str
    password: str


class BaseResponseV1(BaseModel):
    message: str
    status: str = "success"


class SignUpResponseV1(BaseResponseV1):
    email: str


class VerifyResponseV1(BaseResponseV1):
    pass


class LogoutResponseV1(BaseResponseV1):
    pass


class OtpResendResponseV1(BaseResponseV1):
    pass
