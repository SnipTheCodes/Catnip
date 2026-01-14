import asyncio
import atexit
import socket
import subprocess
import time

import psutil


class OllamaClient:
    _started_pid = None

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"
        self.serve()
        atexit.register(self.shutdown)

    @classmethod
    def serve(cls):
        """Start Ollama serve if not already running."""
        for proc in psutil.process_iter(attrs=["name"]):
            if "ollama" in proc.info["name"].lower():
                return
        proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

        cls._started_pid = proc.pid  # track our own instance

        # wait until port is ready
        for _ in range(10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", 11434)) == 0:
                    return
            time.sleep(0.5)
        raise RuntimeError("Failed to start Ollama serve")

    @classmethod
    def shutdown(cls):
        """Stop Ollama when app exits."""
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            if "ollama" in proc.info["name"].lower():
                proc.kill()

    @staticmethod
    async def stream_response(prompt: str):
        proc = await asyncio.create_subprocess_exec(
            "ollama", "run", "llama3", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        async for line in proc.stdout:
            yield line.decode("utf-8", errors="ignore")
