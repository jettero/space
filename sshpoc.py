#!/usr/bin/env python
# coding: utf-8

import argparse
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

import asyncssh
from prompt_toolkit.data_structures import Size
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text

DATA_ROOT = Path("data")
USER_DIR = DATA_ROOT / "user"
MCP_DIR = DATA_ROOT / "mcp"
SERVER_CONFIG = MCP_DIR / "server.json"


class STFU(logging.Filter):
    def filter(self, record):
        if "sshpoc" not in record.pathname:
            return False
        return True


logging.basicConfig(level=logging.DEBUG)
for handler in logging.root.handlers:
    handler.addFilter(STFU())
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))

log = logging.getLogger("sshpoc")
CTRL_D = "\x04"


def canonical_key_text(value) -> str:
    log.debug("canonical_key_text start value_type=%s", type(value))
    if isinstance(value, asyncssh.SSHKey):
        exported = value.export_public_key()
        text = exported.decode() if isinstance(exported, bytes) else exported
    else:
        text = value.decode() if isinstance(value, bytes) else str(value)
    text = text.strip()
    parts = text.split()
    if parts:
        head = parts[0]
        if "~ssh-" in head:
            head = head[head.index("ssh-") :]
        parts[0] = head
        text = " ".join(parts)
    try:
        imported = asyncssh.import_public_key(text)
    except (ValueError, asyncssh.KeyImportError):
        parts = text.split()
        if len(parts) >= 2:
            log.debug("canonical_key_text returning fallback two-part key")
            return f"{parts[0]} {parts[1]}"
        log.debug("canonical_key_text returning fallback single-part key")
        return text
    exported = imported.export_public_key()
    normalized = exported.decode() if isinstance(exported, bytes) else exported
    parts = normalized.strip().split()
    if len(parts) >= 2:
        log.debug("canonical_key_text returning normalized two-part key")
        return f"{parts[0]} {parts[1]}"
    log.debug("canonical_key_text returning normalized single-part key")
    return normalized.strip()


class UserStore:
    def __init__(self, directory: Path = USER_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        log.debug("UserStore init directory=%s", self.directory)

    def path_for(self, username: str) -> Path:
        log.debug("UserStore path_for username=%s", username)
        return self.directory / f"{username}.json"

    def load(self, username: str) -> Optional[Dict[str, object]]:
        log.debug("UserStore load username=%s", username)
        path = self.path_for(username)
        if not path.exists():
            log.debug("UserStore load miss username=%s", username)
            return None
        log.debug("UserStore load hit username=%s", username)
        return json.loads(path.read_text())

    def save(self, user: Dict[str, object]) -> None:
        self.path_for(str(user["username"])).write_text(json.dumps(user, indent=2))
        log.debug("UserStore save username=%s", user["username"])


class HostKeyStore:
    def __init__(self, path: Path = SERVER_CONFIG):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        log.debug("HostKeyStore init path=%s", self.path)

    def load(self) -> Optional[asyncssh.SSHKey]:
        if not self.path.exists():
            log.debug("HostKeyStore load missing key file")
            return None
        payload = json.loads(self.path.read_text())
        key_text = payload.get("host_key")
        if not key_text:
            log.debug("HostKeyStore load missing host_key key")
            return None
        log.debug("HostKeyStore load returning key")
        return asyncssh.import_private_key(key_text)

    def save(self, key: asyncssh.SSHKey) -> None:
        exported = key.export_private_key()
        text = exported.decode() if isinstance(exported, bytes) else exported
        self.path.write_text(json.dumps({"host_key": text}, indent=2))
        log.debug("HostKeyStore save wrote key")


class SignupApp:
    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        users: Optional[UserStore] = None,
        host_keys: Optional[HostKeyStore] = None,
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.users = users or UserStore()
        self.host_keys = host_keys or HostKeyStore()
        key = self.host_keys.load()
        if key is None:
            key = asyncssh.generate_private_key("ssh-rsa")
            self.host_keys.save(key)
        self._host_key = key
        log.debug("SignupApp init host=%s port=%s", listen_host, listen_port)

    @property
    def server_keys(self) -> List[asyncssh.SSHKey]:
        return [self._host_key]

    def register_user(self, username: str, ssh_key: Optional[str]):
        log.debug("register_user username=%s has_key=%s", username, bool(ssh_key))
        existing = self.users.load(username)
        if existing is not None:
            log.debug("register_user duplicate username=%s", username)
            return False, "username already exists"
        if not ssh_key:
            log.debug("register_user missing key username=%s", username)
            return False, "provide a public ssh key"
        canonical = canonical_key_text(ssh_key)
        record = {"username": username, "ssh_keys": [canonical]}
        self.users.save(record)
        log.debug("register_user success username=%s", username)
        return True, record

    def authenticate_key(self, username: str, key) -> Tuple[bool, Optional[Dict[str, object]]]:
        log.debug("authenticate_key username=%s key_type=%s", username, type(key))
        record = self.users.load(username)
        if record is None:
            log.debug("authenticate_key missing_user username=%s", username)
            return False, None
        canonical = canonical_key_text(key) if isinstance(key, str) else canonical_key_text(key.export_public_key())
        stored_raw = record.get("ssh_keys", [])
        stored = [canonical_key_text(item) for item in stored_raw]
        if stored_raw != stored:
            record = dict(record)
            record["ssh_keys"] = stored
            self.users.save(record)
            log.debug("authenticate_key normalized_keys username=%s", username)
        if canonical in stored:
            log.debug("authenticate_key success username=%s", username)
            return True, record
        log.debug("authenticate_key failure username=%s", username)
        return False, None

    def add_key_to_user(self, username: str, key_text: str):
        log.debug("add_key_to_user username=%s", username)
        record = self.users.load(username)
        if record is None:
            log.debug("add_key_to_user missing_user username=%s", username)
            return False
        canonical = canonical_key_text(key_text)
        stored = [canonical_key_text(item) for item in record.get("ssh_keys", [])]
        if canonical not in stored:
            record.setdefault("ssh_keys", []).append(canonical)
            self.users.save(record)
            log.debug("add_key_to_user appended username=%s", username)
        return True


@dataclass
class MenuOption:
    key: str
    label: str
    handler: Callable[["MenuSession"], Awaitable[bool]]


class Menu:
    def __init__(self, title: str, options: List[MenuOption]):
        self.title = title
        self._options = {option.key.lower(): option for option in options}
        log.debug("Menu init title=%s option_keys=%s", title, list(self._options))

    async def run(self, session: "MenuSession") -> bool:
        session.print_line("")
        session.print_line(self.title)
        for option in self._options.values():
            session.print_line(f"  {option.key}) {option.label}")
        choice = await session.prompt_text("> ", raw_prompt=True)
        log.debug("Menu run choice=%s", choice)
        handler = self._options.get(choice.lower())
        if handler is None:
            session.print_line("Select one of the menu options.")
            log.debug("Menu run invalid choice=%s", choice)
            return True
        return await handler.handler(session)


class SignupSSHServer(asyncssh.SSHServer):
    def __init__(self, app: SignupApp):
        self.app = app
        self._preauth = None
        self._preauth_user = None
        self._pending_username = None
        self._pending_record = None
        self._connection_username = None
        self._connection_record = None
        self._authorized_public_keys = []
        log.debug("SignupSSHServer init")

    def begin_auth(self, username: str):
        log.debug("begin_auth username=%s", username)
        self._pending_username = username
        self._preauth = None
        self._preauth_user = None
        self._pending_record = self.app.users.load(username)
        self._connection_username = username
        self._connection_record = None
        self._authorized_public_keys = []
        if self._pending_record is None:
            log.debug("begin_auth no_record username=%s", username)
            return False
        keys = [canonical_key_text(item) for item in self._pending_record.get("ssh_keys", [])]
        if keys:
            self._authorized_public_keys = keys
            log.debug("begin_auth key_auth_required username=%s", username)
            return True
        log.debug("begin_auth no_auth_required username=%s", username)
        return False

    def public_key_auth_supported(self) -> bool:
        supported = bool(self._pending_record and any(self._pending_record.get("ssh_keys") or []))
        log.debug("public_key_auth_supported username=%s supported=%s", self._pending_username, supported)
        return supported

    def validate_public_key(self, username: str, key: asyncssh.SSHKey) -> bool:
        if self._authorized_public_keys:
            key_text = canonical_key_text(key)
            log.debug(
                "validate_public_key checking username=%s key=%s authorized=%s",
                username,
                key_text,
                key_text in self._authorized_public_keys,
            )
            if key_text not in self._authorized_public_keys:
                return False
        success, record = self.app.authenticate_key(username, key)
        if success:
            self._preauth = username
            self._preauth_user = record
            self._connection_record = record
            log.debug("validate_public_key success username=%s", username)
            return True
        log.debug("validate_public_key failure username=%s", username)
        return False

    def auth_completed(self):
        log.debug(
            "auth_completed username=%s has_preauth=%s has_record=%s",
            self._pending_username,
            bool(self._preauth_user),
            bool(self._pending_record),
        )
        if self._preauth_user is None and self._pending_record is not None:
            self._preauth = self._pending_username
            self._preauth_user = self._pending_record
            self._connection_record = self._pending_record

    def session_requested(self):
        username = self._preauth or self._pending_username or self._connection_username
        record = self._preauth_user or self._connection_record
        self._preauth = None
        self._preauth_user = None
        self._pending_username = self._connection_username
        self._pending_record = None
        self._authorized_public_keys = []
        log.debug("session_requested username=%s has_record=%s", username, bool(record))
        return MenuSession(self.app, username, record)

    def connection_lost(self, exc):
        self._preauth = None
        self._preauth_user = None
        self._pending_username = None
        self._pending_record = None
        self._authorized_public_keys = []
        self._connection_username = None
        self._connection_record = None
        log.debug("SignupSSHServer connection_lost exc=%s", exc)


class MenuSession(asyncssh.SSHServerSession):
    def __init__(self, app: SignupApp, username: Optional[str], user_record: Optional[Dict[str, object]]):
        self.app = app
        self.channel = None
        self.username = username
        self.user_record = user_record
        self.prompt_session: Optional[PromptSession] = None
        self.pipe_input_cm = None
        self.pipe_input = None
        self.output_writer = None
        self.output_reader = None
        self.output_forwarder = None
        log.debug("MenuSession init username=%s has_record=%s", username, bool(user_record))

    def connection_made(self, chan):
        self.channel = chan
        self._setup_prompt_toolkit()
        log.debug("MenuSession connection_made username=%s", self.username)

    def shell_requested(self):
        log.debug("MenuSession shell_requested username=%s", self.username)
        return True

    def session_started(self):
        asyncio.create_task(self.run())
        log.debug("MenuSession session_started username=%s", self.username)

    def data_received(self, data, datatype):
        is_bytes = isinstance(data, (bytes, bytearray))
        text = data.decode(errors="ignore") if is_bytes else str(data)
        if CTRL_D in text:
            log.debug("MenuSession ctrl_d username=%s", self.username)
            self._close_io()
            if self.channel is not None:
                self.channel.exit(0)
            return
        if self.pipe_input is not None:
            self.pipe_input.send_text(text)
        log.debug("MenuSession data_received username=%s bytes=%s", self.username, len(text))

    def eof_received(self):
        self._close_io()
        if self.channel is not None:
            self.channel.exit(0)
        return False

    def connection_lost(self, exc):
        self._close_io()
        self.channel = None
        log.debug("MenuSession connection_lost username=%s exc=%s", self.username, exc)

    async def run(self):
        if self.user_record is not None:
            self.username = str(self.user_record.get("username", self.username))
            self.print_line(f"Welcome back, {self.username}.")
            await self.account_menu()
            log.debug("MenuSession run account_menu username=%s", self.username)
            return
        self.print_line("Welcome to the SSH signup PoC.")
        log.debug("MenuSession run guest_menu")
        await self.guest_menu()

    def print_line(self, text: str):
        if self.prompt_session is not None:
            print_formatted_text(text, output=self.prompt_session.app.output)

    async def prompt_text(
        self, label: str, default: Optional[str] = None, *, is_password: bool = False, raw_prompt=False
    ) -> str:
        if self.prompt_session is None:
            return default or ""
        if raw_prompt:
            prompt_text = label
        else:
            prompt_text = label if default is None else f"{label} [{default}]"
            prompt_text = f"{prompt_text}: "
        result = await self.prompt_session.prompt_async(
            prompt_text,
            default=default or "",
            is_password=is_password,
        )
        value = result.strip()
        if value:
            return value
        return default or ""

    async def guest_menu(self):
        signup_option = MenuOption("1", "Sign up", MenuSession.handle_signup)
        login_option = MenuOption("2", "Log in", MenuSession.handle_login)
        quit_option = MenuOption("q", "Exit", MenuSession.handle_quit)
        menu = Menu("Choose an option:", [signup_option, login_option, quit_option])
        repeat = True
        while repeat:
            repeat = await menu.run(self)
            log.debug("guest_menu loop repeat=%s", repeat)

    async def account_menu(self):
        active = True
        while active:
            self.print_line("")
            self.print_line(f"Logged in as {self.username}.")
            self.print_line("Type exit to disconnect or logout to return to the main menu.")
            command = await self.prompt_text("> ", raw_prompt=True)
            normalized = command.lower()
            log.debug("account_menu command=%s", normalized)
            if normalized in {"exit", "quit"}:
                if self.channel is not None:
                    self.channel.exit(0)
                active = False
            elif normalized in {"logout"}:
                self.user_record = None
                await self.guest_menu()
                active = False
            else:
                self.print_line("Use exit or logout.")

    async def handle_signup(self):
        username = self.username
        if not username:
            self.print_line("Reconnect with a username to sign up.")
            log.debug("handle_signup missing_username")
            if self.channel is not None:
                self.channel.exit(1)
            return False
        key_text = await self.prompt_text("Public SSH key")
        log.debug("handle_signup username=%s has_key=%s", username, bool(key_text))
        if not key_text:
            self.print_line("Provide a public SSH key.")
            log.debug("handle_signup no_key username=%s", username)
            return True
        ok, record = self.app.register_user(username, key_text)
        if not ok:
            self.print_line(str(record))
            log.debug("handle_signup failure username=%s", username)
            return True
        self.username = username
        self.user_record = record
        self.print_line("Signup complete. You are now logged in.")
        log.debug("handle_signup success username=%s", username)
        await self.account_menu()
        return False

    async def handle_login(self):
        self.print_line("Reconnect with your SSH credentials to log in.")
        if self.channel is not None:
            self.channel.exit(0)
        log.debug("handle_login exit_prompt username=%s", self.username)
        return False

    async def handle_quit(self):
        if self.channel is not None:
            self.channel.exit(0)
        return False

    def _setup_prompt_toolkit(self):
        self.pipe_input_cm = create_pipe_input()
        self.pipe_input = self.pipe_input_cm.__enter__()
        read_fd, write_fd = os.pipe()
        self.output_reader = read_fd
        self.output_writer = os.fdopen(write_fd, "w", buffering=1, encoding="utf-8", closefd=True)
        log.debug("MenuSession _setup_prompt_toolkit username=%s", self.username)

        def get_size():
            if self.channel is not None:
                try:
                    dims = tuple(self.channel.get_terminal_size())
                except AttributeError:
                    dims = ()
                if len(dims) >= 2 and dims[0] and dims[1]:
                    return Size(rows=dims[1], columns=dims[0])
            return Size(rows=24, columns=80)

        output = Vt100_Output(
            self.output_writer,
            get_size=get_size,
            term=self._terminal_type(),
        )
        self.prompt_session = PromptSession(input=self.pipe_input, output=output)
        self.output_forwarder = asyncio.create_task(self._forward_output())

    def _terminal_type(self):
        if self.channel is None:
            return None
        try:
            return self.channel.get_terminal_type()
        except AttributeError:
            return None

    async def _forward_output(self):
        if self.output_reader is None:
            return
        loop = asyncio.get_running_loop()
        read_pipe = os.fdopen(self.output_reader, "rb", buffering=0, closefd=True)
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        transport, _ = await loop.connect_read_pipe(lambda: protocol, read_pipe)
        try:
            while not reader.at_eof():
                data = await reader.read(1024)
                if not data:
                    break
                if self.channel is not None:
                    self.channel.write(data.decode())
        except asyncio.CancelledError:
            raise
        finally:
            transport.close()
            self.output_reader = None

    def _close_io(self):
        if self.output_forwarder is not None:
            self.output_forwarder.cancel()
            self.output_forwarder = None
        if self.pipe_input is not None:
            self.pipe_input.close()
            self.pipe_input = None
        if self.pipe_input_cm is not None:
            self.pipe_input_cm.__exit__(None, None, None)
            self.pipe_input_cm = None
        if self.output_writer is not None:
            try:
                self.output_writer.close()
            except OSError:
                pass
            self.output_writer = None
        self.prompt_session = None
        log.debug("MenuSession _close_io username=%s", self.username)


def parse_listen(value: str):
    log.debug("parse_listen value=%s", value)
    if ":" in value:
        host, port = value.split(":", 1)
        if port:
            log.debug("parse_listen host=%s port=%s", host, port)
            return host, int(port)
        return host, 2222
    if value.isdigit():
        log.debug("parse_listen default_host port=%s", value)
        return "127.0.0.1", int(value)
    if not value:
        raise ValueError("listen value required")
    return value, 2222


async def run_server(listen: str):
    host, port = parse_listen(listen)
    app = SignupApp(host, port)
    server = await asyncssh.create_server(lambda: SignupSSHServer(app), host, port, server_host_keys=app.server_keys)
    try:
        addr_summary = ", ".join(f"{addr[0]}:{addr[1]}" for addr in server.get_addresses())
        print(f"SSH signup PoC listening on {addr_summary}", flush=True)
        log.debug("run_server listening_on=%s", addr_summary)
        await asyncio.Future()
    finally:
        server.close()
        await server.wait_closed()
        log.debug("run_server closed")


def main():
    parser = argparse.ArgumentParser(description="Minimal SSH signup/login proof of concept.")
    parser.add_argument("--listen", default="127.0.0.1:2222", help="host:port to bind (default 127.0.0.1:2222)")
    args = parser.parse_args()
    try:
        asyncio.run(run_server(args.listen))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
