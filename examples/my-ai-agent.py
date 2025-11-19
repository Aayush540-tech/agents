import os
import asyncio
from livekit.agents import Agent, AgentSession, JobContext, cli, WorkerOptions
from livekit.plugins import deepgram, elevenlabs, silero
from livekit.plugins import groq
from livekit.plugins import openai

from .config import IGNORED_WORDS, INTERRUPTION_COMMANDS, LOW_CONFIDENCE_THRESHOLD
from .IntelligentInterruptHandler import IntelligentInterruptHandler

groq_key = os.environ.get("GROQ_API_KEY")


async def process_ignore_list_command(
    transcript_text: str, interrupt_handler: IntelligentInterruptHandler, session: AgentSession
) -> bool:
    """
    Voice commands supported:
      - "add ignore <word>"
      - "remove ignore <word>"
    """
    lower_text = transcript_text.lower().strip()
    words = lower_text.split()

    if len(words) >= 3 and words[0] in ("add", "remove") and words[1] == "ignore":
        action = words[0]
        word = words[2]

        if action == "add":
            interrupt_handler.add_ignored_word(word)
            confirmation_text = f"I will now ignore the word '{word}'."
        elif action == "remove":
            interrupt_handler.remove_ignored_word(word)
            confirmation_text = f"I will no longer ignore the word '{word}'."
        else:
            return False

        print(f"Voice command: {confirmation_text}")

        # Queue confirmation and speak it explicitly
        session.queue_user_turn(confirmation_text)
        if session.tts and hasattr(session.tts, "speak"):
            await session.tts.speak(confirmation_text)

        return True

    return False


async def async_handle_transcription(transcript_event, interrupt_handler, session):
    transcript_text = transcript_event.text
    transcript_confidence = getattr(transcript_event, "confidence", 1.0)
    agent_is_speaking = session.tts_stream.is_active if session.tts_stream else False

    if await process_ignore_list_command(transcript_text, interrupt_handler, session):
        # Command handled, stop further processing
        return

    if interrupt_handler.should_interrupt(transcript_text, transcript_confidence, agent_is_speaking):
        if agent_is_speaking:
            print("Stopping agent streams due to valid interruption...")
            session.tts_stream.stop()
            session.llm_session.stop()
            session.queue_user_turn(transcript_text)


def main_transcription_handler(transcript_event, interrupt_handler, session):
    # Launch async processing task from sync callback
    asyncio.create_task(async_handle_transcription(transcript_event, interrupt_handler, session))


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    room = ctx.room

    interrupt_handler = IntelligentInterruptHandler(
        ignored_words=IGNORED_WORDS,
        interruption_commands=INTERRUPTION_COMMANDS,
        confidence_threshold=LOW_CONFIDENCE_THRESHOLD,
        persist_file="/Users/ayushrawat/agents/ignored_words.json",
    )

    agent = Agent(
        instructions="You are a friendly agent that pauses gracefully for real interruptions but ignores filler words while speaking."
    )
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3"),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
    )

    await session.start(agent=agent, room=room)

    # Register synchronous callback that starts async transcription handler
    session.on("user_speech_transcribed", lambda event: main_transcription_handler(event, interrupt_handler, session))

    await session.generate_reply(
        instructions="Greet the user and tell them you are ready to talk. Ask them to try interrupting you with 'umm' and then with 'stop'."
    )


if __name__ == "__main__":
    required_env_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "GROQ_API_KEY",
        "DEEPGRAM_API_KEY",
        "ELEVEN_API_KEY",
    ]
    if not all(os.getenv(v) for v in required_env_vars):
        print("ERROR: One or more required environment variables are not set. Ensure GROQ_API_KEY is set.")
        exit(1)

    opts = WorkerOptions(entrypoint_fnc=entrypoint)
    cli.run_app(opts)
