# TranscriptMCP

<div align="center">

**YouTube Video Transcription MCP Server**

Developed by [The Tech Lab](https://github.com/The-TechLab) | [MIT License](./LICENSE)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MCP Version](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

---

## Overview

**TranscriptMCP** is a Model Context Protocol (MCP) server that enables AI assistants to download YouTube videos and transcribe them using OpenAI's Whisper speech recognition model.

This server can be used:
- **Standalone** — Run as a Python script and interact via MCP protocol
- **With OpenClaw** — Integrated as an MCP server for AI assistants

## Features

- 📥 **Download YouTube Audio** — Extract audio from any YouTube video
- 🎙️ **Transcribe with Whisper** — Local, free transcription using Faster Whisper
- 📝 **Multiple Output Formats** — Full transcript with timestamps or plain text
- 💾 **Save Files** — Optionally save the downloaded MP3 and transcript files
- 🔧 **MCP Compatible** — Works with any MCP-compliant AI assistant
- 🆓 **100% Free** — No API keys required (uses local Whisper model)

## Output Files

By default, the server saves:
- **Audio:** `{video_id}.mp3` in the temp directory
- **Transcript:** `{video_id}.txt` in the workspace directory

You can customize where files are saved by modifying the server code.

## Requirements

### System Requirements
- Python 3.11 or higher
- `ffmpeg` (for audio processing)

### Python Packages
- `mcp` — Model Context Protocol server
- `yt-dlp` — YouTube downloader
- `faster-whisper` — Lightning-fast Whisper transcription (recommended)

## Installation

### 1. Install System Dependencies

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
Download ffmpeg from https://ffmpeg.org/download.html and add to PATH.

### 2. Clone the Repository

```bash
git clone https://github.com/The-TechLab/TranscriptMCP.git
cd TranscriptMCP
```

### 3. Install Python Dependencies

```bash
pip install -e .
```

Or with uv:
```bash
uv sync
```

### 4. Download Whisper Model

The first time you run the server, it will automatically download the Whisper model. By default, it uses the `base` model (~140MB).

To use a different model, set the environment variable:
```bash
export WHISPER_MODEL=medium  # Options: tiny, base, small, medium, large
```

## Usage

### Option 1: Standalone MCP Server

Run the server:
```bash
python -m transcript_mcp.server
```

The server communicates via stdin/stdout using the MCP protocol. Connect it to any MCP-compatible AI assistant.

### Option 2: Use with OpenClaw

Add to your OpenClaw MCP configuration (`~/.openclaw/workspace/config/mcporter.json`):

```json
{
  "mcpServers": {
    "transcript": {
      "command": "python",
      "args": [
        "-m",
        "transcript_mcp.server"
      ],
      "env": {
        "WHISPER_MODEL": "base"
      }
    }
  }
}
```

Then restart OpenClaw.

### Option 3: Command Line Testing

Test the server directly:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python -m transcript_mcp.server
```

## Available Tools

### 1. get_video_info

Get metadata about a YouTube video without downloading.

**Parameters:**
- `url` (required): YouTube video URL

**Returns:** Title, description, duration, channel, view count, upload date

### 2. transcribe_video

Download and transcribe a YouTube video with timestamps.

**Parameters:**
- `url` (required): YouTube video URL
- `language` (optional): Language code (e.g., "en"). Auto-detected if not specified.

**Returns:** Full transcript with timestamps for each segment

### 3. transcribe_video_simple

Download and transcribe a YouTube video as plain text.

**Parameters:**
- `url` (required): YouTube video URL
- `language` (optional): Language code (e.g., "en"). Auto-detected if not specified.

**Returns:** Plain text transcript without timestamps

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Whisper model size: tiny, base, small, medium, large |
| `TEMP_DIR` | `/tmp` | Directory for temporary audio files |

## Whisper Models

| Model | Parameters | Size | Relative Speed |
|-------|------------|------|----------------|
| tiny | 39M | 75MB | ~10x |
| base | 74M | 140MB | ~7x |
| small | 244M | 480MB | ~4x |
| medium | 769M | 1.5GB | ~2x |
| large | 1550M | 3GB | 1x |

**Recommendation:** Start with `base` for a good balance of speed and accuracy.

## Example Usage with OpenClaw

Once configured, you can ask your AI:

> "Can you transcribe this video and give me a summary? https://youtube.com/watch?v=xxxxx"

The AI will:
1. Download the audio
2. Transcribe using Whisper
3. Return the transcript or summary

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg (see Installation step 1)

### "Whisper model not found"
The first run will automatically download the model. If it fails, manually run:
```bash
whisper --model base
```

### "Download failed"
- Check the YouTube URL is correct
- Video may be private or region-locked
- Try updating yt-dlp: `pip install -U yt-dlp`

## Development

### Project Structure
```
TranscriptMCP/
├── transcript_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock
```

### Running Tests
```bash
pytest
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License — See [LICENSE](./LICENSE) for details.

---

<div align="center">

**Developed by The Tech Lab**

*Empowering AI with local, private transcription capabilities.*

</div>
