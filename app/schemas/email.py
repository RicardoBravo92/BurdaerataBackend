from pydantic import BaseModel, EmailStr


class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    html: str


class EmailSendResponse(BaseModel):
    success: bool
    message: str


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordRecoveryResponse(BaseModel):
    success: bool
    message: str


class RegistrationEmailRequest(BaseModel):
    email: EmailStr
    user_name: str


class RegistrationEmailResponse(BaseModel):
    success: bool
    message: str