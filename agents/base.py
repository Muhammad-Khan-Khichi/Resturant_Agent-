import logging

from livekit.agents import Agent, RunContext

from userdata import UserData

logger = logging.getLogger("restaurant-example")

RunContext_T = RunContext[UserData]


class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        logger.info(f"entering task {agent_name}")

        userdata: UserData = self.session.userdata
        chat_ctx = self.chat_ctx.copy()

        if isinstance(userdata.prev_agent, Agent):
            truncated_chat_ctx = userdata.prev_agent.chat_ctx.copy(
                exclude_instructions=True,
                exclude_function_call=True,
                exclude_handoff=True,
                exclude_config_update=True,
            ).truncate(max_items=8)
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [
                item for item in truncated_chat_ctx.items if item.id not in existing_ids
            ]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system",
            content=(
                f"[INTERNAL CONTEXT — DO NOT READ ALOUD OR MENTION TO THE USER]\n"
                # f"Agent: {agent_name}\n"
                f"Collected data so far:\n{userdata.summarize()}\n"
                f"Use this silently to continue the conversation. "
                f"Never say 'unknown', never recite this data to the user."
            ),
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply(tool_choice="none")

    async def _transfer_to_agent(
        self, name: str, context: RunContext_T
    ) -> tuple[Agent, str]:
        userdata = context.userdata
        userdata.prev_agent = context.session.current_agent
        next_agent = userdata.agents[name]
        return next_agent, f"Transferring to {name}."