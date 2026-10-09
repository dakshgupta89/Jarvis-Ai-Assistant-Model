# Jarvis AI Voice Assistant

A voice-controlled desktop assistant for **macOS**, written in Python. Clap twice to wake it up, then speak commands to open apps, play music, search the web, control volume, take screenshots, or ask questions to a local AI model (Ollama + Llama 3) that answers by voice.

## Features

- **Double-clap activation**: no wake word needed. Clap twice and Jarvis responds.
- **Voice wake word mode**: optionally say "Jarvis" instead of clapping.
- **Continuous session**: after waking up, Jarvis keeps listening, so you don't need to clap before every command. It goes back to sleep after you stay silent for two turns.
- **System control**: open or close any installed app, open folders, change volume, take screenshots.
- **Web actions**: play songs on YouTube, search YouTube and Google.
- **Info**: current time and date.
- **Local AI chat**: any command that is not a built-in action is sent to Ollama (`llama3`), and the reply is spoken aloud.
- **Startup animation**: shows a GIF in the browser when Jarvis starts.
- **Safe exit and sleep commands**: exact-match, so phrases like "play non stop songs" never shut it down by accident.

## How It Works

```
Sleeping ──(double clap)──► "Yes boss" ──► Listen ──► Process command ──► Speak result
    ▲                                         │                               │
    └────── "go to sleep" / 2 silent turns ───┴───────────────◄──────────────┘
```

1. `wait_for_double_clap()` reads the microphone with PyAudio and detects two loud peaks within 0.15 to 0.8 seconds. The threshold adapts to the room's background noise.
2. `listen_command()` records speech and converts it to text using Google Speech Recognition.
3. `process_command()` matches the text against known commands. If nothing matches, the text goes to the local AI model.
4. `speak()` reads the response aloud using the macOS `say` command.

## Requirements

- macOS (uses `say`, `open`, `osascript`, and `mdfind`)
- Python 3.9 or newer
- A working microphone and an internet connection (for speech recognition and YouTube)
- [Ollama](https://ollama.com) installed and running, with the `llama3` model pulled

## Installation

1. **Clone or download** this project and open the folder in a terminal.

2. **Create a virtual environment** (recommended):

   ```bash
   python3 -m venv venv
   ```

3. **Install PortAudio** (needed by PyAudio):

   ```bash
   brew install portaudio
   ```

4. **Install Python dependencies**:

   ```bash
   ./venv/bin/python -m pip install numpy SpeechRecognition pyaudio pywhatkit pyautogui ollama
   ```

5. **Set up the local AI model**:

   ```bash
   ollama pull llama3
   ```

   Keep the Ollama app running in the background.

6. *(Optional)* Place a GIF named `jarvis_animation.gif` in the project folder for the startup animation.

## Running

```bash
./venv/bin/python jarvis.py
```

Jarvis says "Jarvis is online" and goes to sleep. **Clap twice**, wait for "Yes boss", then speak your command.

To stop the program at any time, say "exit" or press **Ctrl + C** in the terminal.

## macOS Permissions

On first run, allow these in **System Settings → Privacy & Security**:

| Permission | Needed for |
|---|---|
| Microphone | Clap detection and speech recognition |
| Screen Recording | Taking screenshots |

Grant them to the app you run Jarvis from (Terminal or VS Code), then restart that app.

## Voice Commands

### Apps

| Say | Action |
|---|---|
| "open Chrome" / "open Google Chrome" | Opens Google Chrome |
| "open Safari" | Opens Safari |
| "open VS Code" / "open Visual Studio Code" | Opens Visual Studio Code |
| "open WhatsApp" | Opens WhatsApp |
| "open YouTube" | Opens youtube.com in the browser |
| "open Spotify", "open Notes", ... | Opens any installed app by name |
| "close Chrome", "close Spotify", ... | Quits the named app |

### Folders

| Say | Action |
|---|---|
| "open Downloads folder" | Finds the folder with Spotlight and opens it in Finder |
| "open Desktop folder" | Same, for any folder name |

### Music and Search

| Say | Action |
|---|---|
| "play Kesariya" | Plays the song on YouTube |
| "search YouTube for python tutorial" | Opens YouTube search results |
| "search Google for weather today" | Opens Google search results |

### Information

| Say | Action |
|---|---|
| "what time is it" | Speaks the current time |
| "what's the date" / "what day is it" | Speaks today's date |
| "who are you" / "introduce yourself" | Jarvis introduces itself |

### Volume and Screen

| Say | Action |
|---|---|
| "volume up" / "louder" | Increases volume by 15% |
| "volume down" / "quieter" | Decreases volume by 15% |
| "mute" | Mutes the volume |
| "max volume" | Sets volume to 100% |
| "take a screenshot" | Saves to `screenshots/` and opens it |

### Sleep and Exit

| Say | Action |
|---|---|
| "go to sleep" / "sleep" / "standby" | Returns to clap-waiting mode |
| "exit" / "stop" / "bye" / "goodbye" / "shutdown" | Quits the program |
| *(stay silent for two turns)* | Goes to sleep automatically |

### Ask the AI

Anything else is answered by the local AI model. Examples:

- "what is recursion"
- "tell me a joke"
- "explain machine learning in simple words"
- "write a Python function for factorial"

## Configuration

All settings are at the top of `jarvis.py`:

| Setting | Default | Description |
|---|---|---|
| `ASSISTANT_NAME` | `"Jarvis"` | Name used in speech and logs |
| `ACTIVATION_MODE` | `"clap"` | `"clap"` for double clap, `"voice"` for the wake word |
| `WAKE_WORDS` | `jarvis`, `jarvas`, ... | Spellings accepted in voice mode |
| `AI_MODEL` | `"llama3"` | Any model you have pulled in Ollama |
| `GIF_PATH` | `"jarvis_animation.gif"` | Startup animation file |
| `CLAP_MULTIPLIER` | `6.0` | How much louder than background noise a clap must be |
| `CLAP_MIN_THRESHOLD` | `4000` | Minimum loudness to count as a clap |
| `DOUBLE_CLAP_MIN_GAP` / `MAX_GAP` | `0.15` / `0.8` | Allowed time between two claps (seconds) |
| `MAX_SILENT_TURNS` | `2` | Silent turns before going back to sleep |

To change the spoken introduction, edit the `introduce_yourself()` function.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Install the missing package into the same environment you run the script from |
| `pyaudio` fails to install | Run `brew install portaudio` first, then reinstall |
| Claps are not detected | Lower `CLAP_MULTIPLIER` (for example to `4.0`) |
| Wakes up without a clap | Raise `CLAP_MULTIPLIER` (for example to `8.0`) or `CLAP_MIN_THRESHOLD` |
| Jarvis hears nothing | Check microphone permission for Terminal or VS Code |
| "AI is not responding" | Make sure Ollama is running and `ollama pull llama3` has been done |
| A command does nothing | Check the terminal: `Heard: ...` shows what was recognized |
| Screenshot fails | Enable Screen Recording permission |

## Project Structure

```
.
├── jarvis.py                # Main application
├── jarvis_animation.gif     # Startup animation (optional)
├── jarvis_animation.html    # Generated automatically on startup
├── screenshots/             # Created when you take a screenshot
└── README.md
```

## Limitations

- macOS only. Windows and Linux would need replacements for `say`, `open`, `osascript`, and `mdfind`.
- Speech recognition uses Google's online service, so it needs internet.
- Loud background noise can trigger false claps or misheard commands.
- While Jarvis is speaking it does not listen, so wait for it to finish before you talk.

## Ideas for Future Improvements

- WhatsApp message sending and email reading
- Weather and news updates
- Reminders and alarms
- Hand-gesture control using OpenCV and MediaPipe
- Offline speech recognition for use without internet
- Conversation memory so the AI remembers earlier questions

## Tech Stack

Python, SpeechRecognition, PyAudio, NumPy, Ollama (Llama 3), PyWhatKit, PyAutoGUI

## Author

Daksh Gupta