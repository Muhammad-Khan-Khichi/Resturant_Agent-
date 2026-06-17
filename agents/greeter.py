from livekit.agents import RunContext
from livekit.agents.llm import function_tool

from livekit.plugins import openai, elevenlabs 
import os

from agents.base import BaseAgent
from config import VOICES
from userdata import UserData

RunContext_T = RunContext[UserData]


class Greeter(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                f"You are a friendly restaurant receptionist. The menu is: \n"
                "Ask for Reservation or Takeaway"
                "Your ONLY jobs are:\n"
                "1. Greet the caller warmly\n"
                "2. Ask if they want a reservation or takeaway\n"
                "3. Transfer them using ONLY the tools: `to_reservation` or `to_takeaway`\n\n"
                "STRICT RULES:\n"
                "- Never mention the name of the agent you are transferring to. Simply say something like: wait for a second"
                "- NEVER write tool syntax like <function=...> in your speech\n"
                "- NEVER say 'unknown', never recite internal data to the user\n"
                "- Do NOT say the name of agent that you are transferring"
                "- NEVER SAY the name of Agent that you are Transferring"
                "- Never mention the name of the agent you are transferring to"
                "- Do NOT handle orders, payments, or reservations yourself\n"
                "- Transfer immediately once intent is clear\n"
                "- If user asks for checkout or mentions their order is ready, "
                "- call to_takeaway checkout is handled through takeaway\n"
                "- If user already has an order in progress, send them to to_takeaway\n"
                "- If unsure, ask: 'Would you like a reservation or takeaway?'"
            ),
            llm=openai.LLM(
                model="mistral-small-latest",
                base_url="https://api.mistral.ai/v1",
                api_key=os.environ.get("MISTRAL_API_KEY"),
            ),
            tts=elevenlabs.TTS(),
        )

    @function_tool()
    async def to_reservation(self, context: RunContext_T) -> tuple:
        """Called when user wants to make or update a reservation."""
        return await self._transfer_to_agent("reservation", context)

    @function_tool()
    async def to_takeaway(self, context: RunContext_T) -> tuple:
        """Called when the user wants to place a takeaway order,
        wants to continue/complete an existing order,
        or wants to go to checkout."""
        return await self._transfer_to_agent("takeaway", context)