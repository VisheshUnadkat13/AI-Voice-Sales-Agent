import asyncio
import os
import edge_tts

EDGE_VOICE = os.getenv(
    "EDGE_TTS_VOICE",
    "en-IN-NeerjaNeural"
)


# def synthesize(text: str, out_path: str) -> str:
#     """
#     Convert text to speech using Microsoft Edge TTS.
#     Writes an MP3 file to out_path.
#     """

#     asyncio.run(_generate(text, out_path))
#     return out_path

async def synthesize_async(text: str, out_path: str) -> str:
    """
    Async version for FastAPI.
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICE,
    )

    await communicate.save(out_path)
    return out_path


def synthesize(text: str, out_path: str) -> str:
    """
    Sync version for main.py.
    """
    return asyncio.run(synthesize_async(text, out_path))



async def _generate(text: str, out_path: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICE,
    )

    await communicate.save(out_path)