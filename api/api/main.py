import os
import tempfile
import dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from api.chat.chat_handler import ChatHandler
from api.enrich.translation import TranslationHandler
from api.enrich.audio_converter import AudioConverter
from api.enrich.audio_transcriber import AudioTranscriber
import azure.cognitiveservices.speech as speechsdk

import json
import re

dotenv.load_dotenv()

app = FastAPI()

chat_handler = ChatHandler()


class ProcessRequest(BaseModel):
    body: str


class ProcessResponse(BaseModel):
    response: str

class AudioProcessResponse(BaseModel):
    transcribed_audio: str
    response: str


speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get("SPEECH_KEY"),
            region=os.environ.get("SPEECH_REGION")
        )

audio_transcriber = AudioTranscriber(speech_config)
translation_handler = TranslationHandler()

@app.post("/api/process")
async def process(request: ProcessRequest) -> ProcessResponse:
    response_content = str(chat_handler.get_chat_response(request.body))
    return ProcessResponse(response=response_content)

@app.post(path="/api/process-audio-file")
async def process_audio_file(request: ProcessRequest) -> AudioProcessResponse:
                
        # Transcribe audio
        transcribed_audio, detected_language = await audio_transcriber.transcribe_from_audio()

        if len(transcribed_audio) == 0:
            raise HTTPException(
                status_code=400, detail="No audio content found in uploaded file"
            )

        # Send to chat handler
        response_content = str(
            chat_handler.get_chat_response(request.body+'\nUser: '+transcribed_audio)
        )


        print(type(transcribed_audio))
        # Set the voice name, refer to https://aka.ms/speech/voices/neural for full list.
        if  detected_language == "en-GB" or detected_language == "en-IN":
            speech_config.speech_synthesis_voice_name = "en-GB-BellaNeural"
        elif detected_language == "it-IT":
            speech_config.speech_synthesis_voice_name = "it-IT-DiegoNeural"
            target_language = "Italian"
            response_content = translation_handler.translate(response_content, target_language)
        elif detected_language == "pl-PL":
            speech_config.speech_synthesis_voice_name = "pl-PL-MarekNeural"
            target_language = "Polish"
            response_content = translation_handler.translate(response_content, target_language)
        elif detected_language == "es-ES":
            speech_config.speech_synthesis_voice_name = "es-ES-ElviraNeural"
            target_language = "Spanish"
            response_content = translation_handler.translate(response_content,target_language)
        # Uncomment to create a speech synthesizer using the default speaker as audio output.

        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        speech_synthesizer.speak_text_async(response_content).get()

        return AudioProcessResponse(transcribed_audio=transcribed_audio, response=response_content)