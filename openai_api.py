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

app = FastAPI(
    title="Orpheus TTS API",
    description="""
    # Orpheus TTS API
    
    This API provides an OpenAI-compatible interface for the Orpheus Text-to-Speech system.
    
    ## Features
    
    * Generate speech from text with different voices
    * Control speech generation parameters (temperature, top_p, repetition_penalty)
    * Use emotion tags for more expressive speech
    
    ## Usage
    
    You can use this API in a similar way to OpenAI's Text-to-Speech API.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

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
    model: Optional[str] = Field(
        default="orpheus-tts",
        description="The TTS model to use",
        example="orpheus-tts"
    )
    input: str = Field(
        description="The text to generate audio for",
        example="Hello, this is a test of the Orpheus text-to-speech system."
    )
    voice: Optional[str] = Field(
        default=DEFAULT_VOICE,
        description="The voice to use for the generated audio",
        example="tara"
    )
    response_format: Optional[str] = Field(
        default="wav",
        description="The format of the generated audio",
        example="wav"
    )
    speed: Optional[float] = Field(
        default=1.0,
        description="The speed of the generated audio",
        example=1.0
    )
    temperature: Optional[float] = Field(
        default=TEMPERATURE,
        description="Controls randomness in generation (0.0 to 1.0)",
        example=TEMPERATURE
    )
    top_p: Optional[float] = Field(
        default=TOP_P,
        description="Controls diversity of generation (0.0 to 1.0)",
        example=TOP_P
    )
    repetition_penalty: Optional[float] = Field(
        default=REPETITION_PENALTY,
        description="Penalizes repetition (>=1.1 required for stable generation)",
        example=REPETITION_PENALTY
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "input": "Hello, this is a test of the Orpheus text-to-speech system.",
                    "voice": "tara",
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1
                },
                {
                    "input": "Hello, this is a test with emotion tags. <laugh> Isn't that fun?",
                    "voice": "leo",
                    "temperature": 0.7
                }
            ]
        }

class Voice(BaseModel):
    id: str = Field(description="The unique identifier for the voice")
    name: str = Field(description="The display name of the voice")
    description: str = Field(default="", description="A description of the voice")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "tara",
                "name": "Tara",
                "description": "Orpheus TTS voice: tara (recommended)"
            }
        }

class VoicesResponse(BaseModel):
    voices: List[Voice] = Field(
        description="List of available voices for speech synthesis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "voices": [
                    {
                        "id": "tara",
                        "name": "Tara",
                        "description": "Orpheus TTS voice: tara (recommended)"
                    },
                    {
                        "id": "leo",
                        "name": "Leo",
                        "description": "Orpheus TTS voice: leo"
                    }
                ]
            }
        }

class Capability(BaseModel):
    name: str = Field(description="Name of the capability")
    description: str = Field(description="Description of the capability")
    options: Dict[str, Any] = Field(
        default={},
        description="Additional options and parameters for the capability"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "emotion_tags",
                "description": "Emotion tags that can be included in the text",
                "options": {
                    "tags": [
                        "<laugh>", "<chuckle>", "<sigh>", "<cough>", 
                        "<sniffle>", "<groan>", "<yawn>", "<gasp>"
                    ]
                }
            }
        }

class CapabilitiesResponse(BaseModel):
    capabilities: List[Capability] = Field(
        description="List of capabilities supported by the Orpheus TTS system"
    )

# API endpoints
@app.post(
    "/v1/audio/speech",
    response_class=Response,
    tags=["Speech Generation"],
    summary="Generate speech from text",
    description="""
    Generate speech from text using Orpheus TTS.
    Compatible with OpenAI's /v1/audio/speech endpoint.
    
    You can specify different voices and adjust generation parameters.
    """,
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "WAV audio file with the generated speech"
        },
        400: {
            "description": "Bad request, invalid parameters"
        },
        500: {
            "description": "Server error during speech generation"
        }
    }
)
async def create_speech(request: SpeechRequest):
    """
    Generate speech from text using Orpheus TTS.
    
    - **input**: The text to convert to speech
    - **voice**: The voice to use (default: tara)
    - **temperature**: Controls randomness in generation (0.0 to 1.0)
    - **top_p**: Controls diversity of generation (0.0 to 1.0)
    - **repetition_penalty**: Penalizes repetition (>=1.1 required for stable generation)
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

@app.get(
    "/v1/voices",
    response_model=VoicesResponse,
    tags=["Voice Information"],
    summary="List available voices",
    description="Get a list of all available voices for speech synthesis."
)
async def get_voices():
    """
    Returns a list of all available voices that can be used for speech synthesis.
    Each voice has an ID, name, and description.
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

@app.get(
    "/v1/capabilities",
    response_model=CapabilitiesResponse,
    tags=["System Information"],
    summary="Get system capabilities",
    description="Get detailed information about the capabilities of the Orpheus TTS system."
)
async def get_capabilities():
    """
    Returns information about the capabilities of the Orpheus TTS system, including:
    
    - Available voices
    - Emotion tags that can be included in the text
    - Adjustable parameters for speech generation
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

@app.get(
    "/",
    tags=["System Information"],
    summary="API information",
    description="Get basic information about the API."
)
async def root():
    """
    Returns basic information about the API, including the name, version,
    description, and available endpoints.
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
