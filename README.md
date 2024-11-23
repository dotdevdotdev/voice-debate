# VoiceDebate

An AI-powered voice debate application that enables real-time spoken discussions with AI assistants.

## Features

- Real-time speech-to-text using Deepgram
- Natural AI voices using ElevenLabs
- Multiple AI personalities (Socratic Teacher, Devil's Advocate)
- Modern, neon-themed UI
- Support for both desktop and web deployment

## Requirements

- Python 3.9+
- PostgreSQL (for web deployment) or SQLite (for desktop)
- Audio input/output device

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/voice-debate.git
cd voice-debate
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

Edit `.env` with your API keys and configuration.

## Required API Keys

- Deepgram: For speech-to-text ([Get API Key](https://console.deepgram.com/))
- ElevenLabs: For text-to-speech ([Get API Key](https://elevenlabs.io/))
- Anthropic: For Claude AI ([Get API Key](https://console.anthropic.com/))
- OpenAI: For GPT-4 ([Get API Key](https://platform.openai.com/))

## Usage

1. Start the application:
```bash
python -m voicedebate
```

2. Select an AI assistant personality
3. Click the microphone button to start speaking
4. Engage in a debate with your AI partner

## Development

The project structure:

```
voicedebate/
├── __init__.py      # Package initialization
├── config.py        # Configuration management
├── database.py      # Database operations
├── models.py        # Data models
├── speech.py        # Speech services
├── assistant.py     # AI assistant management
└── ui/             # UI components (to be implemented)
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
