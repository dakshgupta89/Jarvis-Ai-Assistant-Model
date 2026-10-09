# 🤖 Jarvis – Python AI Voice Assistant

Jarvis is a Python-based AI voice assistant that wakes up with a **clap** and responds to your voice commands. It uses speech recognition to understand you, a locally running **Ollama (llama3)** model to answer questions, and text-to-speech to talk back.

## ✨ Features

- 👏 **Clap activation** – clap to wake Jarvis up
- 🎙️ **Voice commands** – speak naturally, Jarvis listens and understands
- 🧠 **AI answers via Ollama (llama3)** – ask things like "what is recursion?" or "tell me a joke"
- 🔊 **Text-to-speech replies** – Jarvis speaks the answers out loud
- 💻 **Runs locally** – the LLM runs on your own machine through Ollama

## 🛠️ Tech Stack

- **Language:** Python 3
- **LLM:** Ollama + llama3
- **Speech input:** SpeechRecognition
- **Speech output:** pyttsx3 (text-to-speech)
- **Audio / clap detection:** PyAudio / sounddevice + NumPy

## 📁 Project Structure

```
Jarvis-ai-1.2-main/
├── jarvis.py          # Main file – run this
├── requirements.txt   # Python dependencies
└── README.md
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dakshgupta89/Jarvis-ai.git
   cd Jarvis-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   > On macOS, PyAudio may need PortAudio first: `brew install portaudio`

3. **Install Ollama and pull the model**
   ```bash
   # Download Ollama from https://ollama.com
   ollama pull llama3
   ```

4. **Run Jarvis**
   ```bash
   python jarvis.py
   ```

## 🎯 Usage

1. Make sure Ollama is running in the background.
2. Run `python jarvis.py`.
3. **Clap** to activate Jarvis.
4. Speak your command or question and wait for the reply.

Example commands:
- "What is recursion?"
- "Tell me a joke"
- "Who made you?"

## 🔮 Future Improvements

- Wake word detection ("Hey Jarvis")
- System control (open apps, search the web, set reminders)
- GUI interface
- Multi-language support

## 👥 Authors

Built by Daksh Gupta
