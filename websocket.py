import base64
import os
from dotenv import load_dotenv
import websockets
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Load API key
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

voice_id = "Xb7hH8MSUJpSbSDYk0k2"
model_id = "eleven_flash_v2_5"


class TTSRequest(BaseModel):
    text: str
    audio_name: str   # merged into one body model


async def write_to_local(audio_stream, audio_name: str):
    """Write audio chunks to local mp3 file."""
    os.makedirs("./output", exist_ok=True)
    with open(f"./output/{audio_name}.mp3", "wb") as f:
        async for chunk in audio_stream:
            if chunk:
                f.write(chunk)


async def listen(websocket):
    """Listen for audio data from websocket and yield decoded chunks."""
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)

            if data.get("audio"):
                yield base64.b64decode(data["audio"])  
            elif data.get("isFinal"):
                break

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            break


@app.put("/text_to_speech_ws_streaming")
async def text_to_speech_ws_streaming(req: TTSRequest):
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "text": " ", 
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "use_speaker_boost": False
            },
            "generation_config": {"chunk_length_schedule": [120, 160, 250, 290]},
            "xi_api_key": ELEVENLABS_API_KEY,
        }))

        # Step 2: Send actual text
        await websocket.send(json.dumps({"text": req.text}))

        # Step 3: Signal end of input
        await websocket.send(json.dumps({"text": ""}))

        # Step 4: Listen & save audio
        await write_to_local(listen(websocket), req.audio_name)

    return {"status": "Audio generated", "file": f"./output/{req.audio_name}.mp3"}
