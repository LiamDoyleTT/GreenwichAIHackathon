import os
import struct
from typing import BinaryIO
import azure.cognitiveservices.speech as speechsdk
import time


class AudioTranscriber:
    def __init__(self, speech_config) -> None:
            
        self.speech_config = speech_config

        self.speech_config.speech_recognition_language = "en-US"
   
    async def transcribe_from_audio(self):
        
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)    

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )
        speech_recognition_result = speech_recognizer.recognize_once_async().get()

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(speech_recognition_result.text))
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and endpoint values?")

        return speech_recognition_result.text