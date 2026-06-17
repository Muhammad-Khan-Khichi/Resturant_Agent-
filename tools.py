from typing import Annotated

from livekit.agents import RunContext
from livekit.agents.llm import function_tool
from pydantic import Field
from rag.retriever import search

from userdata import UserData

RunContext_T = RunContext[UserData]

_INVALID_VALUES = {"unknown", "none", "n/a", "", "null"}


def _is_invalid(value: str) -> bool:
    return value.strip().lower() in _INVALID_VALUES


@function_tool()
async def update_name(
    name: Annotated[str, Field(description="The customer's actual name, as spoken by the user")],
    context: RunContext_T,
) -> str:
    """Called when the user provides their name.
    Only call this when the user has actually stated their name.
    Do NOT call with 'unknown' or placeholder values."""
    if _is_invalid(name):
        return "ERROR: Do not call update_name with unknown or placeholder values. Wait for the user to provide their actual name."
    context.userdata.customer_name = name
    return f"Name saved: {name}. Now ask for phone number if not already provided."


@function_tool()
async def update_phone(
    phone: Annotated[str, Field(description="The customer's actual phone number, as spoken by the user")],
    context: RunContext_T,
) -> str:
    """Called when the user provides their phone number.
    Only call this when the user has actually stated their phone number.
    Do NOT call with 'unknown' or placeholder values."""
    if _is_invalid(phone):
        return "ERROR: Do not call update_phone with unknown or placeholder values. Wait for the user to provide their actual phone number."
    context.userdata.customer_phone = phone
    return f"Phone saved: {phone}."


@function_tool()
async def to_greeter(context: RunContext_T):
    """Called when user asks any unrelated questions or requests
    any other services not in your job description."""
    from agents.base import BaseAgent

    curr_agent: BaseAgent = context.session.current_agent
    return await curr_agent._transfer_to_agent("greeter", context)

@function_tool()
async def search_knowledge(query: str,context: RunContext_T,) -> str:
    """Advanced RAG: menu, ingredients, FAQ, policies."""
    
    results = search(query)

    return "\n".join(results)

@function_tool()
async def _calculate_total(self, items: list[str]) -> float:
    """Calculate total by querying ChromaDB for each item's price."""
    import re
    from rag.vectorstore import collection 
    
    collection = collection()
    total = 0.0
    
    for item in items:
        try:
            results = collection.query(
                query_texts=[item],
                n_results=1,
            )
            if results and results["documents"] and results["documents"][0]:
                doc_text = results["documents"][0][0]
                # Extract price like "Price: $5" from the text
                match = re.search(r'Price:\s*\$(\d+\.?\d*)', doc_text)
                if match:
                    total += float(match.group(1))
        except Exception:
            pass
    
    return round(total, 2)