import speech_recognition as sr
import subprocess
import webbrowser
import os
import re
import time
import pyaudio
import numpy as np
import pywhatkit
import ollama
import pyautogui
from datetime import datetime
from urllib.parse import quote_plus

# ============================================================
# CONFIG
# ============================================================
ASSISTANT_NAME = "Jarvis"
CREATOR_NAME = "Daksh"   # introduction me "Created by ..." ke baad ye naam bolega

# "clap"  -> double clap karne par activate hoga
# "voice" -> "Jarvis" bolne par activate hoga
ACTIVATION_MODE = "clap"

WAKE_WORDS = ["jarvis", "jarvas", "jarvic", "service"]

GIF_PATH = "jarvis_animation.gif"
OLD_GIF_PATH = "maya_animation.gif"   # purani file ho to wahi chalegi

AI_MODEL = "qwen2.5:3b"

# Clap detection settings
CLAP_MULTIPLIER = 6.0      # ambient noise ka kitna guna tez awaaz clap maani jaye
CLAP_MIN_THRESHOLD = 4000  # itni se kam awaaz kabhi clap nahi (int16 scale)
DOUBLE_CLAP_MIN_GAP = 0.15 # do claps ke beech minimum gap (sec)
DOUBLE_CLAP_MAX_GAP = 0.8  # do claps ke beech maximum gap (sec)

# Activate hone ke baad kitni baar chup rehne par wapas so jaye
MAX_SILENT_TURNS = 2

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8
recognizer.dynamic_energy_threshold = True

EXIT_PHRASES = {
    "exit", "quit", "stop", "bye", "goodbye", "band karo", "shutdown",
    "stop jarvis", "exit jarvis", "goodbye jarvis", "bye jarvis",
}
SLEEP_PHRASES = {"sleep", "go to sleep", "so jao", "standby"}


# ============================================================
# STARTUP ANIMATION
# ============================================================
def show_startup_gif():
    try:
        gif = GIF_PATH if os.path.exists(GIF_PATH) else OLD_GIF_PATH
        gif_absolute_path = os.path.abspath(gif)

        if not os.path.exists(gif_absolute_path):
            fallback = os.path.abspath("jarvis_fallback_animation.html")
            if os.path.exists(fallback):
                webbrowser.open(f"file://{fallback}")
            else:
                print("💡 Animation file nahi mili, bina animation ke chal raha hai")
            return

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{ASSISTANT_NAME} AI</title>
    <style>
        body {{ margin:0; padding:0; background:black; display:flex;
               justify-content:center; align-items:center; height:100vh; overflow:hidden; }}
        .gif {{ max-width:90vw; max-height:90vh; }}
    </style>
</head>
<body>
    <img src="file://{gif_absolute_path}" alt="{ASSISTANT_NAME}" class="gif">
</body>
</html>"""
        html_file = "jarvis_animation.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        webbrowser.open(f"file://{os.path.abspath(html_file)}")
        print("✅ Animation opened in browser")

    except Exception as e:
        print(f"❌ GIF Error: {e}")


# ============================================================
# SPEAK
# ============================================================
def speak(text):
    try:
        print(f"{ASSISTANT_NAME.lower()}:", text)
        spoken = text if len(text) < 600 else text[:600] + "..."
        subprocess.run(["say", spoken])
    except Exception as e:
        print("Speech Error:", e)


def introduce_yourself():
    speak(
        f"Hello! I am {ASSISTANT_NAME}. Created by {CREATOR_NAME}. "
        "I am smart, fast, and always ready to help. "
        "I can control your system, search anything, play music and write code. "
        "What do you want me to do?"
    )


# ============================================================
# CLAP DETECTION
# ============================================================
def wait_for_double_clap():
    """Double clap sunne tak block karta hai. True return karta hai jab clap mile."""
    RATE = 44100
    CHUNK = 1024

    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                         input=True, frames_per_buffer=CHUNK)

        # Pehle 1 second ambient noise napo
        levels = []
        for _ in range(int(RATE / CHUNK)):
            data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
            levels.append(np.abs(data).max())
        ambient = float(np.mean(levels))
        threshold = max(ambient * CLAP_MULTIPLIER, CLAP_MIN_THRESHOLD)
        print(f"👏 Sleeping... double clap karo (threshold: {int(threshold)})")

        last_clap = 0.0
        while True:
            data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
            peak = np.abs(data).max()
            now = time.time()

            if peak > threshold:
                gap = now - last_clap
                if DOUBLE_CLAP_MIN_GAP < gap < DOUBLE_CLAP_MAX_GAP:
                    print("👏👏 Double clap detected!")
                    return True
                # nayi pehli clap (ya bahut purani thi)
                if gap >= DOUBLE_CLAP_MIN_GAP:
                    last_clap = now
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        pa.terminate()
        time.sleep(0.2)  # mic ko free hone do, taaki speech recognition use kar sake


# ============================================================
# LISTEN
# ============================================================
def listen_command(timeout=5, phrase_time=6):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time)

        text = recognizer.recognize_google(audio, language="en-IN")
        print("Heard:", text)
        return text

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        print("(samajh nahi aaya)")
        return ""
    except sr.RequestError as e:
        print("Internet/Google speech error:", e)
        return ""
    except Exception as e:
        print("Mic Error:", e)
        return ""


def split_wake_word(text):
    """
    "jarvis open chrome" -> (True, "open chrome")
    "exit jarvis"        -> (True, "exit")
    """
    lower = text.lower()
    for w in WAKE_WORDS:
        match = re.search(rf"\b{w}\b", lower)
        if match:
            rest = lower[:match.start()] + " " + lower[match.end():]
            rest = " ".join(rest.split()).strip(" ,.!?")
            return True, rest
    return False, ""


def strip_wake_word(text):
    """Session ke dauraan agar user phir bhi 'jarvis' bole to use hata do."""
    woke, rest = split_wake_word(text)
    return rest if woke else text.lower().strip(" ,.!?")


# ============================================================
# ACTIONS
# ============================================================
def open_folder_anywhere(foldername):
    try:
        result = subprocess.run(["mdfind", "-name", foldername],
                                capture_output=True, text=True)
        results = result.stdout.strip().split("\n")
        folders = [f for f in results if f and os.path.isdir(f)]

        if folders:
            speak("Opening folder")
            subprocess.run(["open", folders[0]])
        else:
            speak("Folder not found boss")
    except Exception as e:
        print("Folder Search Error:", e)
        speak("Error while opening folder")


def open_app(app_name):
    app_name = app_name.strip()
    if not app_name:
        speak("Which app should I open?")
        return
    result = subprocess.run(["open", "-a", app_name.title()], capture_output=True)
    if result.returncode == 0:
        speak(f"Opening {app_name}")
    else:
        speak(f"I could not find an app named {app_name}")


def close_app(app_name):
    app_name = app_name.strip().title()
    result = subprocess.run(["osascript", "-e", f'quit app "{app_name}"'], capture_output=True)
    if result.returncode == 0:
        speak(f"Closing {app_name}")
    else:
        speak(f"I could not close {app_name}")


def get_volume():
    try:
        out = subprocess.run(
            ["osascript", "-e", "output volume of (get volume settings)"],
            capture_output=True, text=True).stdout.strip()
        return int(out)
    except Exception:
        return 50


def set_volume(level):
    level = max(0, min(100, level))
    subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
    return level


def ask_local_ai(prompt):
    try:
        wants_code = any(w in prompt.lower() for w in
                         ["write", "code", "program", "function", "script"])

        if wants_code:
            system = "You are a helpful coding assistant."
        else:
            system = ("You are a voice assistant. Answer in 2 to 3 short, "
                      "simple sentences. No lists, no markdown.")

        response = ollama.chat(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response["message"]["content"]

        # Code wale jawab ko bolne ki jagah file me save karke kholo
        if wants_code:
            os.makedirs("ai_answers", exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            path = os.path.abspath(f"ai_answers/answer_{ts}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(answer)
            subprocess.run(["open", path])
            return "I have written the code and opened it for you."

        return answer

    except Exception as e:
        print("Ollama Error:", e)
        return "Sorry boss, AI is not responding."


def play_song(command):
    try:
        song = command.lower().replace("play", "", 1).strip()
        if not song:
            speak("Please tell me the song name.")
            return
        speak(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)
    except Exception as e:
        print("Play Error:", e)
        speak("Sorry boss")


def take_screenshot():
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.abspath(f"screenshots/screenshot_{timestamp}.png")
    pyautogui.screenshot().save(file_path)
    subprocess.run(["open", file_path])
    return file_path


def has(command, *phrases):
    return any(p in command for p in phrases)


# ============================================================
# COMMAND PROCESSOR
# Return values: "ok" (normal), "exit" (program band), "sleep" (clap ka wait)
# ============================================================
def process_command(command):
    command = command.lower().strip(" ,.!?")
    print("Processing:", command)

    try:
        # --- Exit / Sleep (exact match, taaki "play non stop" jaisi commands na kate) ---
        if command in EXIT_PHRASES:
            speak("Goodbye boss")
            return "exit"

        if command in SLEEP_PHRASES:
            speak("Going to sleep. Clap twice to wake me up.")
            return "sleep"

        # --- Apps ---
        if has(command, "open visual studio code", "open vs code", "open vscode", "open code"):
            speak("Opening Visual Studio Code")
            subprocess.run(["open", "-a", "Visual Studio Code"])

        elif has(command, "open safari"):
            speak("Opening Safari")
            subprocess.run(["open", "-a", "Safari"])

        elif has(command, "open chrome", "open google chrome"):
            speak("Opening Chrome")
            subprocess.run(["open", "-a", "Google Chrome"])

        elif has(command, "open youtube"):
            speak("Opening YouTube")
            webbrowser.open("https://youtube.com")

        elif has(command, "open whatsapp", "open whats app"):
            speak("Opening WhatsApp")
            subprocess.run(["open", "-a", "WhatsApp"])

        # --- Info ---
        elif has(command, "tell me about yourself", "introduce yourself", "who are you"):
            introduce_yourself()

        elif has(command, "what time", "current time", "time kya"):
            speak("It is " + datetime.now().strftime("%I:%M %p"))

        elif has(command, "what date", "today's date", "what day", "aaj kya"):
            speak("Today is " + datetime.now().strftime("%A, %d %B %Y"))

        # --- Volume ---
        elif has(command, "volume up", "increase volume", "louder"):
            speak(f"Volume {set_volume(get_volume() + 15)} percent")

        elif has(command, "volume down", "decrease volume", "lower volume", "quieter"):
            speak(f"Volume {set_volume(get_volume() - 15)} percent")

        elif has(command, "mute"):
            set_volume(0)
            speak("Muted")

        elif has(command, "max volume", "full volume"):
            set_volume(100)
            speak("Volume at maximum")

        # --- Folder / generic app ---
        elif "folder" in command and command.startswith("open"):
            foldername = command.replace("open", "", 1).replace("folder", "").strip()
            open_folder_anywhere(foldername)

        elif command.startswith("open "):
            open_app(command.replace("open", "", 1))

        elif command.startswith("close "):
            close_app(command.replace("close", "", 1))

        # --- Media / Search ---
        elif command.startswith("play "):
            play_song(command)

        elif has(command, "search youtube for"):
            query = command.split("search youtube for", 1)[1].strip()
            speak(f"Searching YouTube for {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")

        elif has(command, "search google for"):
            query = command.split("search google for", 1)[1].strip()
            speak(f"Searching Google for {query}")
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")

        elif has(command, "screenshot", "screen shot"):
            take_screenshot()
            speak("Screenshot taken")

        # --- AI fallback ---
        else:
            speak("Thinking boss")
            speak(ask_local_ai(command))

    except Exception as e:
        print("Command Error:", e)
        speak("Error boss")

    return "ok"


# ============================================================
# SESSION: activate hone ke baad baar-baar commands sunta rahega
# ============================================================
def run_session(first_command=None):
    """
    Commands lagatar sunta hai. Lagatar MAX_SILENT_TURNS baar chup raho to so jaata hai.
    Return: "exit" ya "sleep"
    """
    silent_turns = 0
    pending = first_command

    while True:
        if pending:
            command = pending
            pending = None
        else:
            command = listen_command(timeout=6, phrase_time=8)

        if not command:
            silent_turns += 1
            if silent_turns >= MAX_SILENT_TURNS:
                speak("Going to sleep.")
                return "sleep"
            continue

        silent_turns = 0
        result = process_command(strip_wake_word(command))

        if result in ("exit", "sleep"):
            return result


# ============================================================
# MAIN LOOPS
# ============================================================
def start_jarvis():
    show_startup_gif()
    speak(f"{ASSISTANT_NAME} is online")

    while True:
        try:
            if ACTIVATION_MODE == "clap":
                wait_for_double_clap()
                speak("Yes boss")
                result = run_session()
            else:
                heard = listen_command(timeout=5, phrase_time=5)
                if not heard:
                    continue
                woke, rest = split_wake_word(heard)
                if not woke:
                    continue
                if rest:
                    result = run_session(first_command=rest)
                else:
                    speak("Yes boss")
                    result = run_session()

            if result == "exit":
                break

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("Loop Error:", e)
            time.sleep(1)


if __name__ == "__main__":
    try:
        start_jarvis()
    except KeyboardInterrupt:
        print(f"\n{ASSISTANT_NAME} stopped by user")