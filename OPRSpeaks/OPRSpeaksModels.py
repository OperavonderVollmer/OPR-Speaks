from abc import ABC, abstractmethod
import pyttsx3
import tempfile
import numpy
import wave
import queue
import sounddevice
from OperaPowerRelay import opr
import traceback
import threading
import os
from scipy.io import wavfile


"""
    TTS Model to be used by OpheliaSpeaks
"""

class TTS_Model(ABC):
    """
    Abstract base class for all TTS models

    Methods:
        Say : (text : str) -> bool
            Says the given text
        Demo : () -> None
            Plays a demo of all the available voices
        Start : () -> None
            Starts the TTS engine
        Stop : () -> None
            Stops the TTS engine
    """
    def __init__(self):
        pass

    @abstractmethod
    def _generate_from_text(self, text: str) -> tuple [bytes, int]:
        """
        Generates an audio file from the given text

        Args:
            text (str): The text to generate an audio file from

        Returns:
            tuple [bytes, int]: A tuple containing the generated audio data and the sample rate
        """
        pass

    @abstractmethod
    def Say(self, text: str) -> bool:
        """
        Says the given text

        Args:
            text (str): The text to say

        Returns:
            bool: True if the text was successfully spoken, False otherwise
        """
        pass

    @abstractmethod
    def Demo(self) -> None:
        """
        Demonstrates the available voices by playing a sample message
        with each voice and allows the user to select a preferred voice.

        This method interacts with the user to showcase different voices 
        available in the TTS engine, and updates the selected voice based 
        on user input if desired.
        """
        pass

    @abstractmethod
    def _speak(self, audio_data, sample_rate) -> bool:
        """
        Plays the provided audio data using a sound device.

        Args:
            audio_data (bytes): The audio data to be played.
            sample_rate (int): The sample rate of the audio data.

        Returns:
            bool: True if the audio was played successfully, False if an error occurred.
        """
        pass

    @abstractmethod
    def _tts_thread(self) -> None:
        """
        Abstract method to define the main loop of the TTS engine's thread.

        This method should loop indefinitely and check the speech queue for
        new items. If an item is found, it should be processed and played
        using the _speak method. If no item is found, the method should wait
        until an item is available in the queue.

        This method is intended to be overridden by subclasses of TTS_Model
        that implement the TTS engine's main loop. The main loop should
        be implemented inside this method, and should not be implemented
        in the Start method.

        Returns:
            None
        """
        pass

    @abstractmethod
    def Start(self) -> None:
        """
        Starts the TTS engine.

        This method should start the TTS engine and cause it to start
        processing the speech queue. The method should not block or
        wait until the speech queue is empty, but should return
        immediately after starting the engine.

        Returns:
            None
        """
        pass

    @abstractmethod
    def Stop(self) -> None:
        """
        Stops the TTS engine.

        This method should stop the TTS engine and ensure that the speech queue 
        is no longer being processed. It should also handle any necessary cleanup 
        to properly terminate the TTS engine's operation.

        Returns:
            None
        """
        pass

class pyttsx3_TTS(TTS_Model):
    def __init__(self, speaker_index: str, voice_index: int = 1):
        super().__init__()

        self._engine = pyttsx3.init('sapi5')
        self.voices = self._engine.getProperty('voices')
        self._voice_index = voice_index or 1
        self._engine.setProperty('voice', self.voices[int(self._voice_index)].id)
        self._speech_queue = queue.Queue()
        self._speaker_index = int(speaker_index)
        self._running = False
        self._speaking_thread = None

        opr.print_from("OPR-Speaks-Models - Initialize", "SUCCESS: PYTTX3 TTS Model initialized")

    def Demo(self) -> None:
        voices = self._engine.getProperty('voices')

        msg = "This is a test message to demonstrate the sound of the voices"

        for voice in voices:
            opr.print_from("OPR-Speaks-Models - Demo Voice", f"Name: {voice.name}")
            self._engine.setProperty('voice', voice.id)
            self._engine.say(msg)
            self._engine.runAndWait()
            self._engine.stop()
        

        _ = opr.input_from("OPR-Speaks-Models - Demo Voice", "Would you like to change the voice? (y/n)")

        if _.lower() == "y":     
            while True:
                try:
                    voice_list = "\n".join(f"{idx + 1} -> {voice.name}" for idx, voice in enumerate(voices))
                    opr.print_from("OPR-Speaks-Models - Demo Voice", f"Available voices:\n{voice_list}")


                    choice = opr.input_from("OPR-Speaks-Models - Demo Voice", "Please select a voice by entering its index")

                    if choice.isdigit() and (1 <= int(choice) <= len(voices)):
                        break

                except ValueError:
                    opr.print_from("OPR-Speaks-Models - Demo Voice", "Invalid input. Please enter a valid voice index.")
            
            self._voice_index = int(choice) - 1

        self._engine.setProperty('voice', voices[int(self._voice_index)].id)

        self._engine.say("This is the voice you have selected")
        self._engine.runAndWait()
        self._engine.stop()

        opr.print_from("OPR-Speaks-Models - Demo Voice", "SUCCESS: Demo voice completed")



    def _generate_from_text(self, text: str) -> tuple[bytes, int]:

        if not text.strip():
            opr.print_from("OPR-Speaks-Models - Generate From Text", "FAILED: No text provided")
            return None, None

        fileName = None  # Ensure fileName exists before assignment

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                fileName = temp_wav.name  # Ensure filename is assigned

            self._engine.save_to_file(text, fileName)
            self._engine.runAndWait()      

            sample_rate, audio_data = wavfile.read(fileName)
            return audio_data, sample_rate

        except Exception:
            error_message = traceback.format_exc()
            opr.print_from("OPR-Speaks-Models - Generate From Text", f"FAILED: Unexpected Error while generating audio: {error_message}")
            return None, None

        finally:
            if fileName and os.path.exists(fileName):  
                try:
                    os.remove(fileName)
                except Exception as e:
                    opr.print_from("OPR-Speaks-Models - Generate From Text", f"WARNING: Failed to delete temp file {fileName}: {e}")


    def Say(self, text: str) -> bool:
        
        try:
            audio_data, sample_rate = self._generate_from_text(text)
            if audio_data is None or sample_rate is None:
                return False

            item = audio_data, sample_rate
            self._speech_queue.put(item)
            return True
        except:
            return False
        

    def _speak(self, audio_data, sample_rate) -> bool:
        try:
            sounddevice.play(data = audio_data, samplerate = sample_rate, device = self._speaker_index)
            sounddevice.wait()
            return True
        except Exception:
            error_message = traceback.format_exc()
            opr.print_from("OPR-Speaks-Models - Speak", f"FAILED: Unexpected Error while speaking: {error_message}")
            return False

    
    def _tts_thread(self) -> None:
        while self._running:
            try:
                item = self._speech_queue.get(block=True)
                if item is None:  
                    break

                audio_data, sample_rate = item
                if self._speak(audio_data, sample_rate):
                    opr.print_from("OPR-Speaks-Models - TTS Thread", "SUCCESS: Speaking")                
                
                self._speech_queue.task_done()
            except queue.Empty:
                pass


    def Start(self) -> None:
        if self._running:
            return

        self._running = True
        self._speaking_thread = threading.Thread(target=self._tts_thread, daemon=True)
        self._speaking_thread.start()
        opr.print_from("OPR-Speaks-Models - Start", "SUCCESS: TTS Thread started")

    def Stop(self) -> None:
        if not self._running:  
            return  

        self._running = False
        self._speech_queue.put(None)  
        self._speaking_thread.join()
        opr.print_from("OPR-Speaks-Models - Stop", "SUCCESS: TTS Thread stopped")


def TTS_Factory(speaker_index: str, model: str = "", voice_index: int = None) -> TTS_Model:

    if not model:
        model = opr.input_from("OPR-Speaks-Models - Factory", "Select a model:\n1. PYTTX3 TTS\nInput")

    match model:
        case "1": 
            return pyttsx3_TTS(speaker_index, voice_index)
        case _:
            opr.print_from("OPR-Speaks-Models - Factory", "FAILED: Invalid model selected")
            return None


if __name__ == "__main__":
    
    opr.print_from("OPR-Speaks-Models - Main", "Running OPR-Speaks-Models...")
    
    try:
        TTS = TTS_Factory(18)

        while True:
            decision = opr.input_from("OPR-Speaks-Models - Main", "Select an action:\n1. Start\n2. Configure Voice\nInput")
            if decision == "1":
                break
            elif decision == "2":
                TTS.Demo()

        TTS.Start()
        while True:
            decision = opr.input_from("OPR-Speaks-Models - Main", "Input (Say STOP_THIS to stop)")
            if decision == "STOP_THIS":
                TTS.Stop()
                break
            TTS.Say(decision)
        
    except KeyboardInterrupt:
        pass

    except Exception:
        error_message = traceback.format_exc()
        opr.print_from("OPR-Speaks-Models - Main", f"FAILED: Unexpected Error: {error_message}")

    TTS.Stop()

    opr.print_from("OPR-Speaks-Models - Main", "Stopping OPR-Speaks-Models...")