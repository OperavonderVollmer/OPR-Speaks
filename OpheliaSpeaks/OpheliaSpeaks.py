import queue
import sounddevice
from OperaPowerRelay import opr
import os
import models
import traceback

"""

    Ophelia Speaks

    Mostly a staging module for the models, direct interaction is done by retrieving the model from the factory

"""

OUTPUT_DEVICE = None

def _select_speaker() -> tuple[int, str]:
    devices = sounddevice.query_devices()

    output_devices = [(d['index'], d['name']) for d in devices if d['max_output_channels'] > 0]

    if not output_devices:
        opr.print_from("Ophelia Speaks - Select Speaker", "No output devices found.", 2)
        return -1, "None"

    speaker_list = "\n" + "\n".join(f"{idx+1} -> {name}" for idx, (dev_id, name) in enumerate(output_devices))

    while True:
        opr.print_from("Ophelia Speaks - Select Speaker", speaker_list, 2)
        speaker_choice = opr.input_from("Ophelia Speaks - Select Speaker", "No selected speaker selected. Please select from the above")

        if not speaker_choice.isdigit() or not 1 <= int(speaker_choice) <= len(output_devices):
            opr.print_from("Ophelia Speaks - Select Speaker", "Invalid Input")
            continue

        selected_index,  selected_speaker = output_devices[int(speaker_choice) - 1]
        print(f"Selected Speaker: {selected_speaker} | Index: {selected_index}")
        return selected_index, selected_speaker

def _prepare_speaker(config_file: dict, speaker_index: str = "", speaker_name: str = "") -> None:
    
    if speaker_index and speaker_name:
        selected_index, selected_speaker = speaker_index, speaker_name
        config_file["selected_speaker"] = selected_index, selected_speaker

    else:
        try:
            selected_index, selected_speaker = config_file["selected_speaker"]
        except KeyError:
            selected_index, selected_speaker, = _select_speaker()
            config_file["selected_speaker"] = selected_index, selected_speaker

    opr.save_json("Ophelia Speaks - Initialize", os.path.dirname(os.path.abspath(__file__)), config_file, "config.json")
    opr.print_from("Ophelia Speaks - Initialize", f"Selected Speaker: {selected_speaker}")
    
    global OUTPUT_DEVICE
    OUTPUT_DEVICE = selected_index, selected_speaker

def initialize(speaker_index: str = "", speaker_name: str = "") -> None:
    
    """
    Initializes the Ophelia Speaks setup by loading configuration and 
    preparing the speaker.

    This function loads the configuration from a JSON file and sets up 
    the speaker using the provided or pre-configured speaker index and 
    name. If no speaker is selected, it prompts the user to select one 
    and updates the configuration file accordingly.

    Args:
        speaker_index (str, optional): The index of the speaker to be 
        used. Defaults to an empty string, which triggers the selection 
        process.
        
        speaker_name (str, optional): The name of the speaker to be 
        used. Defaults to an empty string.
    """

    config_file = opr.load_json("Ophelia Speaks - Initialize", os.path.dirname(os.path.abspath(__file__)))
    _prepare_speaker(config_file, speaker_index, speaker_name)

def get_TTS(model: str = "") -> models.TTS_Model:
    """
    Retrieves a TTS Model from the factory using the provided model name.

    Args:
        model (str, optional): The name of the model to be used. Defaults to an empty string.

    Returns:
        models.TTS_Model: The retrieved TTS Model
    """
    return models.TTS_Factory(OUTPUT_DEVICE[0], model)

initialize()


if __name__ == "__main__":
    opr.print_from("Ophelia Speaks - Main", "Starting Ophelia Speaks Demonstration...")

    try:
        TTS: models.TTS_Model = get_TTS()

        while True:
            decision = opr.input_from("Ophelia Speaks - Main", "Select an action:\n1. Start\n2. Configure Voice\nInput")
            if decision == "1":
                break
            elif decision == "2":
                TTS.Demo()

        TTS.Start()
        while True:
            decision = opr.input_from("Ophelia Speaks - Main", "Input (Say STOP_THIS to stop)")
            if decision == "STOP_THIS":
                TTS.Stop()
                break
            TTS.Say(decision)
        
    except KeyboardInterrupt:
        pass

    except Exception:
        error_message = traceback.format_exc()
        opr.print_from("Ophelia Speaks - Main", f"FAILED: Unexpected Error: {error_message}")

    TTS.Stop()

    opr.print_from("Ophelia Speaks - Main", "Stopping Ophelia Speaks...")