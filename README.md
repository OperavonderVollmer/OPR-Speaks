# OPR-Speaks

**OPR-Speaks** is a Python-based Text-to-Speech (TTS) system designed for seamless voice synthesis. It provides an interface for speech generation, voice selection, and real-time playback, making it suitable for various automation and accessibility applications.

## Features
- **Text-to-Speech Conversion:** Converts input text into high-quality speech.
- **Voice Selection:** Choose from available voices to customize the output.
- **Real-Time Playback:** Streams generated speech directly to an audio output device.
- **Queue-Based Processing:** Ensures smooth execution of multiple speech requests.
- **Error Handling & Logging:** Detects and reports issues efficiently.

## Installation

### Prerequisites

- Python 3.x
- Required dependencies (install using pip):
  ```sh
  pip install pyttsx3 numpy sounddevice scipy git+https://github.com/OperavonderVollmer/OperaPowerRelay.git@v1.1.5
  ```

### Manual Installation

1. Clone or download the repository.
2. Navigate to the directory containing `setup.py`:
   ```sh
   cd /path/to/OPR-Speaks
   ```
3. Install the package in **editable mode**:
   ```sh
   pip install -e .
   ```

### Installing via pip:

```sh
pip install git+https://github.com/OperavonderVollmer/OPR-Speaks.git@main
```

Ensure that all necessary dependencies are installed in your environment.
## Usage

```python
from OPRSpeaks import OPRSpeaks

TTS = OPRSpeaks.get_TTS()
TTS.Start()
TTS.Say("Hello world!")
TTS.Stop()
```

## Dependencies
- `pyttsx3`
- `sounddevice`
- `scipy`

## License
This project is licensed under the MIT License.

## Contribution
Feel free to submit issues, suggestions, or pull requests to improve OPR-Speaks.

## Acknowledgments
Special thanks to OpenAI and contributors for their support in speech synthesis advancements.

