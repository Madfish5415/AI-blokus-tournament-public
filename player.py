import asyncio
import os
import sys


class Player:
    def __init__(self, path):
        print(path)
        if not os.path.exists(path):
            raise ValueError(path)
        self.path = path
        self.proc = None

    async def create(self):
        self.proc = await asyncio.create_subprocess_exec(
            self.path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr)

    async def read_stdout(self):
        buf = await self.proc.stdout.readline()
        if not buf:
            return None
        print("GAME: RECEIVE FROM {}: {}".format(self.proc.pid, buf.decode('utf-8')), file=sys.stderr)
        return buf.decode("utf-8")

    async def read_stderr(self):
        buf = await self.proc.stderr.readline()
        if not buf:
            return None
        print("GAME: RECEIVE FROM {}: {}".format(self.proc.pid, buf.decode('utf-8')), file=sys.stderr)
        return buf.decode("utf-8")

    async def write_stdin(self, msg):
        print("GAME: SEND TO {}: {}".format(self.proc.pid, msg), file=sys.stderr)
        self.proc.stdin.write(bytes(msg, "utf-8"))
        await self.proc.stdin.drain()
        await asyncio.sleep(0.5)

    def terminate(self):
        self.proc.terminate()
