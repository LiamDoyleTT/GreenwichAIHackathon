import os
import struct
from typing import BinaryIO
import azure.cognitiveservices.speech as speechsdk
import time


class AudioTranscriber:
    def __init__(self, speech_config) -> None:
            
        self.speech_config = speech_config

        self.speech_config.speech_recognition_language = "en-GB"
   
    async def transcribe_from_audio(self):
        
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)    
        
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-GB", "it-IT", "pl-PL", "en-IN"])

        translation_config = speechsdk.translation.SpeechTranslationConfig(
            speech_recognition_language='en-GB',
            target_languages=('it', 'pl')
            )
        
        
        # Creates a translation recognizer using and audio file as input.
        speech_recognizer = speechsdk.translation.TranslationRecognizer(
            speech_config=self.speech_config,
            translation_config=translation_config, 
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config
            )
        
        speech_recognition_result = speech_recognizer.recognize_once_async().get()
        detectedSrcLang = ""
        
        # Check the result
        if speech_recognition_result.reason == speechsdk.ResultReason.TranslatedSpeech:
            print("""Recognized: {}
            German translation: {}
            French translation: {}""".format(
        speech_recognition_result.text, speech_recognition_result.translations['it'], speech_recognition_result.translations['pl']))
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(speech_recognition_result.text))
            detectedSrcLang = speech_recognition_result.properties[speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult]
            print("Detected Language: {}".format(detectedSrcLang))
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and endpoint values?")

       
        if detectedSrcLang == "it-IT":
            return speech_recognition_result.translations['it'], detectedSrcLang
        elif detectedSrcLang == "pl-PL":
            return speech_recognition_result.translations['pl'], detectedSrcLang
        else: 
            return speech_recognition_result.text, detectedSrcLang
        
            
        
    