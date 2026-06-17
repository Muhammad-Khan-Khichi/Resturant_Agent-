from typing import Annotated
import os
from livekit.agents import RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, elevenlabs

from pydantic import Field

from agents.base import BaseAgent
from config import VOICES
from tools import update_name, update_phone, to_greeter, _is_invalid
from userdata import UserData

RunContext_T = RunContext[UserData]


class Checkout(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                f"You are a checkout agent at a restaurant. The menu is:\n"
                "Your job is to collect information step by step in this exact order:\n"
                "1. Confirm the total expense using confirm_expense\n"
                "2. Collect customer name using update_name\n"
                "3. Collect customer phone using update_phone\n"
                "4. Collect credit card number, expiry, and CVV using update_credit_card\n"
                "5. Confirm checkout using confirm_checkout\n\n"
                "- Never mention the name of the agent you are transferring to. Simply say something like: wait for a second"
                "CRITICAL RULES:\n"
                "- Ask for ONE piece of information at a time. Wait for the user to respond.\n"
                "- NEVER call any tool with 'unknown', 'none', or placeholder values.\n"
                "- NEVER output raw function call syntax like `function_name>{...}</function>`"
                "- NEVER SAY the name of Agent that you are Transferring"
                "- NEVER mention function names, XML tags, or technical syntax to the user"
                "- Always respond in natural, conversational language"
                "- Use the provided tools silently - the user should never see tool syntax"
                "- NEVER write tool syntax like <function=...> in your speech\n"
                "- Do NOT say the name of agent that you are transferring"
                "- Only call a tool when the user has ACTUALLY provided that specific value.\n"
                "- For update_credit_card: only call it when you have ALL THREE values "
                "(number, expiry AND cvv) from the user. Ask for them one by one.\n"
                "- NEVER call to_greeter unless the user explicitly says they want to cancel.\n"
                "- NEVER transfer to checkout again you are already in checkout.\n"
                "- If the user seems frustrated, calmly ask for the next missing piece only."
                "- When order is PROCESSED SPEAK THAT YOUR ORDER IS PROCESSED"
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
    async def confirm_expense(
        self,
        expense: Annotated[float, Field(description="The total cost of the order in dollars")],
        context: RunContext_T,
    ) -> str:
        """Called to confirm the total cost before collecting payment.
        Calculate from the order items in userdata."""
        context.userdata.expense = expense
        return f"Expense confirmed: ${expense}. Now ask for customer name."

    @function_tool()
    async def update_credit_card(
        self,
        number: Annotated[str, Field(description="The actual credit card number spoken by the user")],
        expiry: Annotated[str, Field(description="The actual expiry date spoken by the user, e.g. 12/26")],
        cvv: Annotated[str, Field(description="The actual 3-digit CVV spoken by the user")],
        context: RunContext_T,
    ) -> str:
        """Called ONLY when the user has provided ALL THREE values: card number, expiry, AND cvv.
        Ask for each value separately first. Only call this function once you have all three.
        NEVER call with 'unknown', 'none', or any placeholder for ANY field."""
        errors = []
        if _is_invalid(number):
            errors.append("card number")
        if _is_invalid(expiry):
            errors.append("expiry date")
        if _is_invalid(cvv):
            errors.append("CVV")

        if errors:
            missing = ", ".join(errors)
            return (
                f"ERROR: Missing real values for: {missing}. "
                f"Ask the user to provide {missing} before calling this tool again."
            )

        userdata = context.userdata
        userdata.customer_credit_card = number
        userdata.customer_credit_card_expiry = expiry
        userdata.customer_credit_card_cvv = cvv
        last4 = number[-4:] if len(number) >= 4 else number
        return f"Card saved ending in {last4}. Now call confirm_checkout."

    @function_tool()
    async def confirm_checkout(self, context: RunContext_T) -> str | tuple:
        """Called only when ALL fields are collected:
        expense, customer name, phone, card number, expiry, and CVV."""
        userdata = context.userdata
        if not userdata.expense:
            return "Cannot checkout: confirm the expense first."
        if not userdata.customer_name:
            return "Cannot checkout: ask for the customer's name first."
        if not userdata.customer_phone:
            return "Cannot checkout: ask for the customer's phone number first."
        if (
            not userdata.customer_credit_card
            or not userdata.customer_credit_card_expiry
            or not userdata.customer_credit_card_cvv
        ):
            return "Cannot checkout: collect the full credit card details first."
        userdata.checked_out = True
        return await to_greeter(context)

    @function_tool()
    async def to_takeaway(self, context: RunContext_T) -> tuple:
        """Called ONLY when the user explicitly wants to go back and change their order."""
        return await self._transfer_to_agent("takeaway", context)