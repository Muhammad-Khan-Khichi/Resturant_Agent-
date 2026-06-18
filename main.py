import logging
import os

from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, cli
from livekit.plugins import assemblyai, cartesia, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from agents import Checkout, Greeter, Reservation, Takeaway
from userdata import UserData


from api.database import AsyncSessionLocal, init_db
from api import db_service

load_dotenv()
logging.basicConfig(level=logging.INFO)

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    userdata = UserData()
    userdata.agents.update(
        {
            "greeter": Greeter(),
            "reservation": Reservation(),
            "takeaway": Takeaway(),
            "checkout": Checkout(),
        }
    )

    room_name = ctx.room.name

    async with AsyncSessionLocal() as db:
        await db_service.create_session(
            db,
            room_name=room_name,
            participant_name="customer",
        )

    session = AgentSession[UserData](
        userdata=userdata,
        stt=assemblyai.STT(),
        llm=openai.LLM(
            model="mistral-small-latest",
            base_url="https://api.mistral.ai/v1",
            api_key=os.environ.get("MISTRAL_API_KEY"),
        ),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        max_tool_steps=5,
    )


    @session.on("user_input_transcribed")
    async def on_user_message(event):
        if event.is_final:
            async with AsyncSessionLocal() as db:
                await db_service.save_message(
                    db,
                    room_name=room_name,
                    role="user",
                    content=event.transcript,
                )

    @session.on("agent_speech_committed")
    async def on_agent_message(event):
        agent_name = session.current_agent.__class__.__name__
        async with AsyncSessionLocal() as db:
            await db_service.save_message(
                db,
                room_name=room_name,
                role="assistant",
                content=event.audio_transcript,
                agent_name=agent_name,
            )

    @session.on("session_ended")
    async def on_session_end(event):
        async with AsyncSessionLocal() as db:
            await db_service.save_userdata(db, room_name, userdata)
            if userdata.checked_out:
                await db_service.save_checkout(db, room_name, userdata)
            await db_service.end_session(db, room_name)

    await session.start(
        agent=userdata.agents["greeter"],
        room=ctx.room,
    )



if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    cli.run_app(server)