#!/usr/bin/env python3
"""
TranscriptMCP - YouTube Video Transcription Server
An MCP server that downloads YouTube videos and transcribes them using Whisper.

Developed by The Tech Lab
License: MIT

Usage:
    python -m transcript_mcp.server
    
Or with custom settings:
    WHISPER_MODEL=base python -m transcript_mcp.server
"""

import base64
import json
import os
import sys
import tempfile
import subprocess
import asyncio
from pathlib import Path

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Configuration
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
TEMP_DIR = os.environ.get("TEMP_DIR", "/tmp")

server = Server("transcript-mcp")


def get_video_info(url: str) -> dict:
    """Get video information using yt-dlp"""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                url
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "success": True,
                "title": data.get("title", "Unknown"),
                "description": data.get("description", "")[:500],
                "duration": data.get("duration", 0),
                "uploader": data.get("uploader", "Unknown"),
                "upload_date": data.get("upload_date", "Unknown"),
                "view_count": data.get("view_count", 0),
                "channel_id": data.get("channel_id", ""),
                "channel_url": data.get("channel_url", ""),
            }
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_audio(url: str, output_path: str) -> dict:
    """Download YouTube audio to a file"""
    try:
        # Use best audio quality, extract to mp3
        result = subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--output", output_path,
                "--no-playlist",
                "--quiet",
                "--no-warnings",
                url
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for download
        )
        
        if result.returncode == 0:
            # Find the downloaded file
            base = output_path.replace(".%(ext)s", "")
            for ext in ['.mp3', '.m4a', '.wav', '.webm']:
                if os.path.exists(base + ext):
                    return {"success": True, "path": base + ext}
            return {"success": False, "error": "Downloaded file not found"}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    """Transcribe audio using Faster Whisper"""
    try:
        from faster_whisper import WhisperModel
        
        # Load model (cached after first load)
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        
        # Transcribe
        segments, info = model.transcribe(audio_path, language=language)
        
        # Collect all text
        text = ""
        segments_list = []
        for seg in segments:
            text += seg.text + " "
            segments_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            })
        
        return {
            "success": True,
            "text": text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": segments_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MCP tools"""
    return [
        types.Tool(
            name="get_video_info",
            description="Get information about a YouTube video (title, description, duration, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube video URL"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="transcribe_video",
            description="Download a YouTube video and transcribe it using Whisper. Returns the full transcript with timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube video URL"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en' for English). Leave empty for auto-detection.",
                        "default": None
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="transcribe_video_simple",
            description="Download and transcribe a YouTube video. Returns just the text transcript without timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "YouTube video URL"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en' for English). Leave empty for auto-detection.",
                        "default": None
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    url = arguments.get("url")
    language = arguments.get("language")
    
    if not url:
        return [types.TextContent(type="text", text="Error: URL is required")]
    
    if name == "get_video_info":
        info = get_video_info(url)
        if info.get("success"):
            result = f"""Video Information:
Title: {info['title']}
Channel: {info['uploader']}
Duration: {info['duration']//60} min {info['duration']%60} sec
Views: {info['view_count']:,}
Upload Date: {info['upload_date']}

Description:
{info['description'][:500]}"""
            return [types.TextContent(type="text", text=result)]
        else:
            return [types.TextContent(type="text", text=f"Error: {info.get('error', 'Unknown error')}")]
    
    elif name in ["transcribe_video", "transcribe_video_simple"]:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=TEMP_DIR) as tmp:
            audio_path = tmp.name + ".mp3"
        
        try:
            # Download audio
            download_result = download_audio(url, audio_path)
            if not download_result.get("success"):
                return [types.TextContent(type="text", text=f"Download error: {download_result.get('error', 'Unknown error')}")]
            
            actual_path = download_result["path"]
            
            # Transcribe
            transcribe_result = transcribe_audio(actual_path, language)
            
            if not transcribe_result.get("success"):
                return [types.TextContent(type="text", text=f"Transcription error: {transcribe_result.get('error', 'Unknown error')}")]
            
            if name == "transcribe_video_simple":
                # Return just the text
                return [types.TextContent(type="text", text=transcribe_result["text"])]
            else:
                # Return with timestamps
                segments = transcribe_result.get("segments", [])
                output = f"Transcript ({transcribe_result.get('language', 'unknown')}):\n\n"
                for seg in segments[:50]:  # First 50 segments
                    mins = int(seg["start"]) // 60
                    secs = int(seg["start"]) % 60
                    output += f"[{mins:02d}:{secs:02d}] {seg['text']}\n"
                
                if len(segments) > 50:
                    output += f"\n... ({len(segments) - 50} more segments)"
                
                return [types.TextContent(type="text", text=output)]
        
        finally:
            # Cleanup
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if 'actual_path' in locals() and os.path.exists(actual_path):
                    os.remove(actual_path)
            except:
                pass
    
    return [types.TextContent(type="text", text="Unknown tool")]


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
