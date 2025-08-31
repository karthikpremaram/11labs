import base64
import json
import logging
import os

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_stream")

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
voice_id = "Xb7hH8MSUJpSbSDYk0k2"
model_id = "eleven_flash_v2_5"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    text: str
    audio_name: str = "stream"


@app.post("/stream_tts")
async def stream_tts(req: TTSRequest):
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"

    async def audio_iterator():
        async with websockets.connect(uri) as websocket:
            # 1. Initialization
            await websocket.send(
                json.dumps(
                    {
                        "text": " ",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.8,
                            "use_speaker_boost": False,
                        },
                        "generation_config": {
                            "chunk_length_schedule": [120, 160, 250, 290]
                        },
                        "xi_api_key": ELEVENLABS_API_KEY,
                    }
                )
            )
            logger.info("Initialization message sent")

            # 2. Send desired text with trigger flag
            await websocket.send(
                json.dumps({"text": req.text, "try_trigger_generation": True})
            )
            logger.info("Synthesizing text")

            # 3. End of input signal
            await websocket.send(json.dumps({"text": ""}))
            logger.info("End of input sent")

            # 4. Stream and yield decoded audio chunks
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get("audio"):
                    yield base64.b64decode(data["audio"])

                if data.get("isFinal"):
                    logger.info("Received final audio chunk; exiting")
                    break

    return StreamingResponse(audio_iterator(), media_type="audio/mpeg")
