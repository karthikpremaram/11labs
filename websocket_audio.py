import json
import logging
import os

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Load API key
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

voice_id = "Xb7hH8MSUJpSbSDYk0k2"
model_id = "eleven_flash_v2_5"


class TTSRequest(BaseModel):
    text: str
    audio_name: str


async def listen_and_collect(websocket):
    """Listen for audio data from websocket and collect Base64 chunks."""
    audio_chunks = []
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)

            if data.get("audio"):
                audio_chunks.append(data["audio"])  # Store as Base64 string
            elif data.get("isFinal"):
                break

        except websockets.exceptions.ConnectionClosed:
            logging.warning("Connection closed")
            break

    return audio_chunks


@app.put("/text_speech_stream")
async def text_to_speech_ws_streaming(req: TTSRequest):
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model_id}"
    logging.info(f"Connecting to {uri}")
    async with websockets.connect(uri) as websocket:
        # Step 1: Initialize connection
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
        logging.info("WebSocket connection initialized.")

        # Step 2: Send actual text
        await websocket.send(json.dumps({"text": req.text}))
        logging.info("Text sent for synthesis")

        # Step 3: Signal end of input
        await websocket.send(json.dumps({"text": ""}))
        logging.info("End of text signal sent.")

        # Step 4: Listen & collect audio chunks
        audio_chunks = await listen_and_collect(websocket)
        logging.info(f"Collected {len(audio_chunks)} audio chunks.")

        # Step 5: Save to JSON
        os.makedirs("./output", exist_ok=True)
        json_path = f"./output/{req.audio_name}.json"
        with open(json_path, "w") as f:
            json.dump({"audio_chunks": audio_chunks}, f)
        logging.info(f"Audio chunks saved to {json_path}")

    return {"status": "Audio chunks saved in JSON", "file": json_path}
