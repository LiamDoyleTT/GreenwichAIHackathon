import os
import struct
from typing import BinaryIO
import azure.cognitiveservices.speech as speechsdk
import time
import random


class AudioTranscriber:
    def __init__(self, speech_config) -> None:
            
        self.speech_config = speech_config

        self.speech_config.speech_recognition_language = "en-US"
   
    async def transcribe_from_audio(self):
        
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)    
        
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-GB", "it-IT", "pl-PL", "en-IN"])

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
            auto_detect_source_language_config = auto_detect_source_language_config,
        )
        speech_recognition_result = speech_recognizer.recognize_once_async().get()
        detectedSrcLang = ""
        
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

        # languages_codes = ["fr-FR", "en-GB", "ar-MA", "es-ES", "it-IT", "pl-PL", "en-IN"]
        
        # wired_translated = speech_recognition_result.text+" Please answer only in the language with language code "+random.choice(languages_codes)
        language = "en-GB"
        if detectedSrcLang == "it-IT":
            language = "Italian"
        elif detectedSrcLang == "pl-PL":
            language = "Polish"
            
        wired_translated = speech_recognition_result.text+" Please translate the answer in "+language
            
        return speech_recognition_result.text, detectedSrcLang, wired_translated 
    
    
    def translate_answer():
        
        weatherfilename="en-us_zh-cn.wav"

        # set up translation parameters: source language and target languages
        translation_config = speechsdk.translation.SpeechTranslationConfig(
            speech_recognition_language='en-US',
            target_languages=('de', 'fr'))
        audio_config = speechsdk.audio.AudioConfig(filename=weatherfilename)

        # Specify the AutoDetectSourceLanguageConfig, which defines the number of possible languages
        auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "de-DE", "zh-CN"])

        # Creates a translation recognizer using and audio file as input.
        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config, 
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect_source_language_config)

        # Starts translation, and returns after a single utterance is recognized. The end of a
        # single utterance is determined by listening for silence at the end or until a maximum of 15
        # seconds of audio is processed. The task returns the recognition text as result.
        # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
        # shot recognition like command or query.
        # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
        result = recognizer.recognize_once()

        # Check the result
        if result.reason == speechsdk.ResultReason.TranslatedSpeech:
            print("""Recognized: {}
            German translation: {}
            French translation: {}""".format(
                result.text, result.translations['de'], result.translations['fr']))
        elif result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(result.text))
            detectedSrcLang = result.properties[speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult]
            print("Detected Language: {}".format(detectedSrcLang))
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            print("Translation canceled: {}".format(result.cancellation_details.reason))
            if result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(result.cancellation_details.error_details))