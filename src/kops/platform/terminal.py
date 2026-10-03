"""WebSocket terminal: a pty running `sandbox.terminal_argv(target)`."""
from __future__ import annotations

import asyncio
import codecs
import fcntl
import json
import logging
import os
import pty
import signal
import struct
import subprocess
import termios

from fastapi import WebSocket, WebSocketDisconnect

log = logging.getLogger("kops.terminal")


def _scrubbed_env() -> dict:
    """Nothing from the platform's own environment (secrets) reaches the candidate's shell."""
    return {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp"),
            "TERM": "xterm-256color", "LANG": "C.UTF-8"}


def _set_size(fd: int, cols: int, rows: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def _kill(proc: subprocess.Popen) -> None:
    for sig in (signal.SIGHUP, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        try:
            proc.wait(timeout=1)
            break
        except subprocess.TimeoutExpired:
            continue
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


async def serve_terminal(ws: WebSocket, argv: list[str]) -> None:
    """Pump bytes between the (already accepted) WebSocket and a pty child until either ends."""
    master, slave = pty.openpty()
    _set_size(master, 80, 24)
    proc = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, env=_scrubbed_env(),
                            start_new_session=True, close_fds=True,
                            preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0))
    os.close(slave)
    loop = asyncio.get_running_loop()
    out: asyncio.Queue = asyncio.Queue()

    def on_readable() -> None:
        try:
            data = os.read(master, 65536)
        except OSError:
            data = b""
        if not data:
            loop.remove_reader(master)
        out.put_nowait(data)

    loop.add_reader(master, on_readable)

    async def pump_out() -> None:
        dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
        while True:
            data = await out.get()
            if not data:
                return
            await ws.send_text(json.dumps({"t": "o", "d": dec.decode(data)}))

    async def pump_in() -> None:
        while True:
            try:
                msg = json.loads(await ws.receive_text())
            except (WebSocketDisconnect, RuntimeError):
                return
            except ValueError:
                continue
            if msg.get("t") == "i":
                os.write(master, str(msg.get("d", "")).encode())
            elif msg.get("t") == "r":
                try:
                    _set_size(master, int(msg["c"]), int(msg["r"]))
                except (KeyError, ValueError, TypeError, OSError):
                    pass

    t_out, t_in = asyncio.create_task(pump_out()), asyncio.create_task(pump_in())
    try:
        done, _ = await asyncio.wait({t_out, t_in}, return_when=asyncio.FIRST_COMPLETED)
        if t_out in done:    # the shell ended: report its exit code, then close
            code = await loop.run_in_executor(None, lambda: proc.wait(timeout=5)) if proc.poll() is None else proc.returncode
            try:
                await ws.send_text(json.dumps({"t": "x", "code": code}))
                await ws.close()
            except Exception:
                pass
    except subprocess.TimeoutExpired:
        pass
    finally:
        for t in (t_out, t_in):
            t.cancel()
        loop.remove_reader(master)
        await loop.run_in_executor(None, _kill, proc)
        try:
            os.close(master)
        except OSError:
            pass
