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

    @classmethod
    def serve(cls):
        """
        Start Ollama serve if not already running.
        This method should be called explicitly by the application.
        """
        if cls._started_pid is not None:
            return
        proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

        cls._started_pid = proc.pid

        # wait until port is ready
        for _ in range(10):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", 11434)) == 0:
                    return
            time.sleep(0.5)
        raise RuntimeError("Failed to start Ollama serve")

    @classmethod
    def shutdown(cls):
        """Stop Ollama serve started by this app."""

        if cls._started_pid is None:
            return
        try:
            proc = psutil.Process(cls._started_pid)
            proc.terminate()
        except psutil.NoSuchProcess:
            pass
        finally:
            cls._started_pid = None

    @staticmethod
    async def stream_response(prompt: str):
        """Run the Ollama CLI with the given prompt and yield streamed response lines."""

        proc = await asyncio.create_subprocess_exec("ollama", "run", "llama3",
                                                    prompt,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE, )
        async for line in proc.stdout:
            yield line.decode("utf-8", errors="ignore")
