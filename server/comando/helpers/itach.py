import socket
import time


class ITach:
    def __init__(self, ip_address: str):
        self.ip_address = ip_address

    def send(
        self,
        command: str | list[str],
        interval_seconds: int = 0.1,
    ) -> None | bytes:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((self.ip_address, 4999))
            s.send(b"CRT\r")
            if not isinstance(command, list):
                command = [command]
            for cmd in command:
                if interval_seconds:
                    time.sleep(interval_seconds)
                s.send(cmd.encode("ascii"))
                s.send(b"\r")

            data = s.recv(1024)
            return data.rstrip().decode("ascii")
