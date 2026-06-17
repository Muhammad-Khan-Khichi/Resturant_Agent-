from typing import Annotated

from livekit.agents import RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import elevenlabs
import os
import smtplib
from email.mime.text import MIMEText

from livekit.plugins import openai
from pydantic import Field

from agents.base import BaseAgent
from config import VOICES
from tools import update_name, update_phone, to_greeter
from userdata import UserData

from dotenv import load_dotenv
load_dotenv()

RunContext_T = RunContext[UserData]


class Reservation(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a reservation agent at a restaurant. Your job is to ask for "
                "the reservation time, then customer's name, phone number, and email. "
                "FIRST CONFIRM THE NAME PHONE NUMBER AND EMAIL THEN SEND THE EMAIL"
                "Then confirm the reservation details with the customer and send a confirmation email."
            ),
            llm=openai.LLM(
                model="mistral-small-latest",
                base_url="https://api.mistral.ai/v1",
                api_key=os.environ.get("MISTRAL_API_KEY"),
            ),
            tools=[update_name, update_phone, to_greeter],
            tts=elevenlabs.TTS(),
        )

    @function_tool()
    async def update_reservation_time(
        self,
        time: Annotated[str, Field(description="The reservation time")],
        context: RunContext_T,
    ) -> str:
        """Called when the user provides their reservation time.
        Confirm the time with the user before calling the function."""
        context.userdata.reservation_time = time
        return f"The reservation time is updated to {time}"

    @function_tool()
    async def update_email(
        self,
        email: Annotated[str, Field(description="Customer email address")],
        context: RunContext_T,
    ) -> str:
        """Store customer's email."""
        context.userdata.customer_email = email
        return f"Email saved as {email}."

    @function_tool()
    async def send_confirmation_email(
        self,
        email: Annotated[str, Field(description="Customer email")],
        name: Annotated[str, Field(description="Customer name")],
        time: Annotated[str, Field(description="Reservation time")],
    ) -> str:
        """Send reservation confirmation email."""

        subject = "Your Restaurant Reservation Confirmation 🍽️"
        body = f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0; padding:0; background:#f6f6f6; font-family:Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="padding:30px 0;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0" role="presentation"
                 style="background:#ffffff; border-radius:12px; overflow:hidden;">
            <tr>
              <td style="background:#111827; padding:22px; text-align:center;">
                <h1 style="color:#ffffff; margin:0;">🍽️ Reservation Confirmed</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:30px; color:#333;">
                <p style="font-size:16px;">
                  Hi <strong>{name}</strong>,
                </p>
                <p style="font-size:15px; line-height:1.6;">
                  Your table has been successfully reserved.
                </p>
                <table width="100%" style="margin-top:20px; background:#f3f4f6; padding:15px; border-radius:8px;">
                  <tr>
                    <td style="font-size:14px;">
                      📅 <strong>Time:</strong> {time}<br/>
                      🪑 <strong>Status:</strong> Confirmed<br/>
                      📍 <strong>Location:</strong> Main Dining Area
                    </td>
                  </tr>
                </table>
                <p style="margin-top:25px; font-size:14px;">
                  See you soon,<br/>
                  <strong>The Restaurant Team</strong> ✨
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#f9fafb; padding:12px; text-align:center; font-size:12px; color:#888;">
                Automated confirmation email
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = os.environ.get("EMAIL_FROM")
        msg["To"] = email

        with smtplib.SMTP(os.environ.get("SMTP_HOST"), 587) as server:
            server.starttls()
            server.login(
                os.environ.get("SMTP_USER"),
                os.environ.get("SMTP_PASS"),
            )
            server.send_message(msg)

        return "Confirmation email sent successfully."

    @function_tool()
    async def confirm_reservation(self, context: RunContext_T) -> str | tuple:
        """Called when the user confirms the reservation."""
        userdata = context.userdata
        if not userdata.customer_name or not userdata.customer_phone:
            return "Please provide your name and phone number first."
        if not userdata.reservation_time:
            return "Please provide reservation time first."
        if not userdata.customer_email:
            return "Please provide your email address first."

        await self.send_confirmation_email(
            email=userdata.customer_email,
            name=userdata.customer_name,
            time=userdata.reservation_time,
        )
        return await self._transfer_to_agent("greeter", context)