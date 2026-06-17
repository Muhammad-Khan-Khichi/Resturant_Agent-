import logging
import os
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, cli
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import openai
from livekit.plugins import deepgram, cartesia

from agents import Greeter, Reservation, Takeaway, Checkout
from userdata import UserData

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

    session = AgentSession[UserData](
        userdata=userdata,
        stt=deepgram.STT(model="deepgram/nova-3"),
        llm=openai.LLM(
            model="mistral-small-latest",
            base_url="https://api.mistral.ai/v1",
            api_key=os.environ.get("MISTRAL_API_KEY"),
        ),
        tts=cartesia.TTS(model="cartesia/sonic-3"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(), 
        max_tool_steps=5,
    )

    await session.start(
        agent=userdata.agents["greeter"],
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(server)


