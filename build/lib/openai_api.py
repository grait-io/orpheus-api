import os
import io
import time
import wave
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Import functions from gguf_orpheus
from gguf_orpheus import (
    generate_speech_from_api,
    AVAILABLE_VOICES,
    DEFAULT_VOICE,
    TEMPERATURE,
    TOP_P,
    REPETITION_PENALTY,
    list_available_voices
)

app = FastAPI(title="Orpheus TTS API", description="OpenAI-compatible API for Orpheus TTS")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API requests and responses
class SpeechRequest(BaseModel):
    model: Optional[str] = "orpheus-tts"
    input: str
    voice: Optional[str] = DEFAULT_VOICE
    response_format: Optional[str] = "wav"
    speed: Optional[float] = 1.0
    temperature: Optional[float] = TEMPERATURE
    top_p: Optional[float] = TOP_P
    repetition_penalty: Optional[float] = REPETITION_PENALTY

class Voice(BaseModel):
    id: str
    name: str
    description: str = ""

class VoicesResponse(BaseModel):
    voices: List[Voice]

class Capability(BaseModel):
    name: str
    description: str
    options: Dict[str, Any] = {}

class CapabilitiesResponse(BaseModel):
    capabilities: List[Capability]

# API endpoints
@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest):
    """
    Generate speech from text using Orpheus TTS.
    Compatible with OpenAI's /v1/audio/speech endpoint.
    """
    if not request.input:
        raise HTTPException(status_code=400, detail="Text input is required")
    
    if request.voice not in AVAILABLE_VOICES:
        raise HTTPException(status_code=400, detail=f"Voice '{request.voice}' not available. Use /v1/voices to see available voices.")
    
    if request.response_format != "wav":
        raise HTTPException(status_code=400, detail="Only 'wav' response format is supported")
    
    # Create a temporary file to store the audio
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    temp_file = f"temp_{request.voice}_{timestamp}.wav"
    
    try:
        # Generate speech
        generate_speech_from_api(
            prompt=request.input,
            voice=request.voice,
            output_file=temp_file,
            temperature=request.temperature,
            top_p=request.top_p,
            repetition_penalty=request.repetition_penalty
        )
        
        # Read the generated WAV file
        with open(temp_file, "rb") as f:
            audio_data = f.read()
        
        # Delete the temporary file
        os.remove(temp_file)
        
        # Return the audio data with appropriate headers
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={request.voice}_{timestamp}.wav"}
        )
    
    except Exception as e:
        # Clean up if an error occurs
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/v1/voices")
async def get_voices():
    """
    Get a list of available voices.
    """
    voices = []
    for voice_id in AVAILABLE_VOICES:
        voice = Voice(
            id=voice_id,
            name=voice_id.capitalize(),
            description=f"Orpheus TTS voice: {voice_id}" + (" (recommended)" if voice_id == DEFAULT_VOICE else "")
        )
        voices.append(voice)
    
    return VoicesResponse(voices=voices)

@app.get("/v1/capabilities")
async def get_capabilities():
    """
    Get information about the capabilities of the Orpheus TTS system.
    """
    capabilities = [
        Capability(
            name="voices",
            description="Available voices for speech synthesis",
            options={
                "available_voices": AVAILABLE_VOICES,
                "default_voice": DEFAULT_VOICE
            }
        ),
        Capability(
            name="emotion_tags",
            description="Emotion tags that can be included in the text",
            options={
                "tags": [
                    "<laugh>", "<chuckle>", "<sigh>", "<cough>", 
                    "<sniffle>", "<groan>", "<yawn>", "<gasp>"
                ]
            }
        ),
        Capability(
            name="parameters",
            description="Adjustable parameters for speech generation",
            options={
                "temperature": {
                    "default": TEMPERATURE,
                    "min": 0.0,
                    "max": 1.0,
                    "description": "Controls randomness in generation"
                },
                "top_p": {
                    "default": TOP_P,
                    "min": 0.0,
                    "max": 1.0,
                    "description": "Controls diversity of generation"
                },
                "repetition_penalty": {
                    "default": REPETITION_PENALTY,
                    "min": 1.0,
                    "max": 2.0,
                    "description": "Penalizes repetition (>=1.1 required for stable generation)"
                }
            }
        )
    ]
    
    return CapabilitiesResponse(capabilities=capabilities)

@app.get("/")
async def root():
    """
    Root endpoint with basic information about the API.
    """
    return {
        "name": "Orpheus TTS API",
        "version": "0.1.0",
        "description": "OpenAI-compatible API for Orpheus TTS",
        "endpoints": [
            {"path": "/v1/audio/speech", "method": "POST", "description": "Generate speech from text"},
            {"path": "/v1/voices", "method": "GET", "description": "List available voices"},
            {"path": "/v1/capabilities", "method": "GET", "description": "Get system capabilities"}
        ]
    }

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("openai_api:app", host="127.0.0.1", port=8000, reload=True)
