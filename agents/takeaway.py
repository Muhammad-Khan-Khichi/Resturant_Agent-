from typing import Annotated
import os
from livekit.agents import RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, elevenlabs
from pydantic import Field

from agents.base import BaseAgent
from config import VOICES
from tools import to_greeter, search_knowledge, calculate_total
from userdata import UserData

RunContext_T = RunContext[UserData]


class Takeaway(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                f"You are a takeaway agent that takes orders from the customer. "
                f"Our menu is: \n\n"
                "Your job:\n"
                "1. Ask what the customer wants to order\n"
                "2. Call update_order when they specify items\n"
                "3. Confirm the order and total price\n"
                "4. When customer confirms they are done, call to_checkout\n\n"
                "STRICT RULES:\n"
                "- Never mention the name of the agent you are transferring to. Simply say something like: wait for a second"
                "- NEVER say 'unknown' or recite internal data to the user\n"
                "- NEVER SAY the name of Agent that you are Transferring"
                "- Never mention the name of the agent you are transferring to"
                "- NEVER call update_order and to_checkout in the same turn\n"
                "- Call to_checkout ONLY after update_order is done and customer confirms\n"
                "- Do NOT mention checkout until customer says they are done ordering"
                "- WHEN YOU REPEAT THE PHONE NUMBER DON'T SAY ONE HUNDRED TWENTY FOUR say like 03011238094"
            ),
            llm=openai.LLM(
                model="mistral-small-latest",
                base_url="https://api.mistral.ai/v1",
                api_key=os.environ.get("MISTRAL_API_KEY"),
            ),
            tools=[to_greeter, search_knowledge],
            tts=elevenlabs.TTS(),
        )

    @function_tool()
    async def update_order(
        self,
        items: Annotated[list[str], Field(description="The items of the full order")],
        context: RunContext_T,
    ) -> str:
        """Called when the user specifies what they want to order.
        Only call this do NOT call to_checkout in the same turn."""
        context.userdata.order = items
        total = calculate_total(items)
        return f"Order updated: {items}. Total: ${total}. Ask if they want anything else."

    @function_tool()
    async def to_checkout(self, context: RunContext_T) -> str | tuple:
        """Called ONLY when the customer confirms their order is complete
        and they are ready to pay. Do NOT call update_order before this in the same turn."""
        if not context.userdata.order:
            return "No order found. Please take the customer's order first."
        return await self._transfer_to_agent("checkout", context)
