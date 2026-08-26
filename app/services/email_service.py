import resend
from app.core.config import get_settings

resend.api_key = get_settings().RESEND_API_KEY


class EmailService:
    def __init__(self):
        self.from_email = "Burdaerata <onboarding@resend.dev>"

    async def send_password_recovery(
        self, to_email: str, user_name: str, recovery_link: str
    ) -> dict:
        """Send password recovery email in English."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h1 style="color: #333; text-align: center;">Password Recovery</h1>
                <p style="color: #555; font-size: 16px;">Hello {user_name},</p>
                <p style="color: #555; font-size: 16px;">We received a request to reset your password for your Burdaerata account.</p>
                <p style="color: #555; font-size: 16px;">Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{recovery_link}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;">Reset Password</a>
                </div>
                <p style="color: #555; font-size: 16px;">If you didn't request this, please ignore this email.</p>
                <p style="color: #555; font-size: 16px;">This link will expire in 24 hours.</p>
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">Burdaerata - The Card Game</p>
            </div>
        </body>
        </html>
        """

        params = {
            "from": self.from_email,
            "to": [to_email],
            "subject": "Password Recovery - Burdaerata",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        return {"success": True, "id": email.id}

    async def send_registration_success(
        self, to_email: str, user_name: str
    ) -> dict:
        """Send successful registration email in English."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <h1 style="color: #333; text-align: center;">Welcome to Burdaerata!</h1>
                <p style="color: #555; font-size: 16px;">Hello {user_name},</p>
                <p style="color: #555; font-size: 16px;">Thank you for joining Burdaerata! Your account has been created successfully.</p>
                <p style="color: #555; font-size: 16px;">You're now ready to play the most hilarious card game with your friends!</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://burdaerata.vercel.app" style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-size: 16px;">Start Playing</a>
                </div>
                <p style="color: #555; font-size: 16px;">Here's what you can do:</p>
                <ul style="color: #555; font-size: 16px;">
                    <li>Create a game and invite friends</li>
                    <li>Join existing games with a code</li>
                    <li>Play with hilarious answer cards</li>
                </ul>
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">Burdaerata - The Card Game</p>
            </div>
        </body>
        </html>
        """

        params = {
            "from": self.from_email,
            "to": [to_email],
            "subject": "Welcome to Burdaerata!",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        return {"success": True, "id": email.id}


email_service = EmailService()