import asyncio
import os
import types

import asyncssh
import pytest

import sshpoc


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    user_dir = tmp_path_factory.mktemp("user_store")
    host_path = tmp_path_factory.mktemp("host_store") / "host.json"
    yield sshpoc.SignupApp(
        "127.0.0.1",
        0,
        users=sshpoc.UserStore(user_dir),
        host_keys=sshpoc.HostKeyStore(host_path),
    )


@pytest.mark.parametrize("username", ["alice", "bob"])
def test_unknown_user_hits_menu(username, app):
    server1 = sshpoc.SignupSSHServer(app)
    assert server1.begin_auth(username) is False
    session1 = server1.session_requested()
    assert session1.username == username
    assert session1.user_record is None
    assert server1.begin_auth(username) is False
    server1.session_requested()
    server1.connection_lost(None)

    server2 = sshpoc.SignupSSHServer(app)
    assert server2.begin_auth(username) is False
    session2 = server2.session_requested()
    assert session2.username == username
    assert session2.user_record is None


@pytest.mark.parametrize("username", ["charlie", "dana"])
def test_key_authenticated_user_auto_logs_in(username, app):
    key = asyncssh.generate_private_key("ssh-ed25519")
    app.register_user(username, key.export_public_key().decode())

    def connect_once():
        server = sshpoc.SignupSSHServer(app)
        assert server.begin_auth(username)
        assert server.validate_public_key(username, key)
        server.auth_completed()
        session = server.session_requested()
        assert session.username == username
        assert session.user_record["username"] == username
        server.connection_lost(None)

    connect_once()
    connect_once()


@pytest.mark.parametrize("username", ["erin", "frank"])
def test_wrong_or_missing_key_rejected(username, app):
    good_key = asyncssh.generate_private_key("ssh-ed25519")
    app.register_user(username, good_key.export_public_key().decode())
    bad_key = asyncssh.generate_private_key("ssh-ed25519")

    server = sshpoc.SignupSSHServer(app)
    assert server.begin_auth(username)
    assert server.validate_public_key(username, bad_key) is False
    assert server.validate_public_key(username, good_key)
    server.connection_lost(None)


@pytest.mark.parametrize("username", ["george", "hana"])
def test_signup_refreshes_future_auth(username, app):
    server = sshpoc.SignupSSHServer(app)
    assert server.begin_auth(username) is False
    session = server.session_requested()
    assert session.username == username
    assert session.user_record is None
    key = asyncssh.generate_private_key("ssh-ed25519")
    app.register_user(username, key.export_public_key().decode())
    assert server.begin_auth(username)
    assert server.validate_public_key(username, key)
    server.auth_completed()
    authed_session = server.session_requested()
    assert authed_session.user_record["username"] == username
    server.connection_lost(None)


@pytest.mark.parametrize("username", ["isaac", "jill"])
def test_deleted_user_no_longer_authenticates(username, app):
    key = asyncssh.generate_private_key("ssh-ed25519")
    app.register_user(username, key.export_public_key().decode())
    server = sshpoc.SignupSSHServer(app)
    assert server.begin_auth(username)
    assert server.validate_public_key(username, key)
    server.connection_lost(None)
    os.remove(app.users.path_for(username))
    server2 = sshpoc.SignupSSHServer(app)
    assert server2.begin_auth(username) is False
    assert server2.validate_public_key(username, key) is False


@pytest.mark.parametrize("username", ["kai", "lena"])
def test_signup_via_session_then_login(username, app):
    server = sshpoc.SignupSSHServer(app)
    assert server.begin_auth(username) is False
    session = server.session_requested()
    key = asyncssh.generate_private_key("ssh-ed25519")
    key_text = key.export_public_key().decode()

    async def fake_prompt_text(label, default=None, *, is_password=False, raw_prompt=False):
        if "Public SSH key" in label:
            return key_text
        return "exit"

    session.prompt_text = fake_prompt_text

    class FakeChannel:
        def __init__(self):
            self.code = None

        def exit(self, code):
            self.code = code

        def close(self):
            pass

        async def wait_closed(self):
            return

        def get_terminal_size(self):
            return 80, 24

        def get_terminal_type(self):
            return "xterm"

    channel = FakeChannel()

    async def drive():
        session.connection_made(channel)
        await session.handle_signup()

    asyncio.run(drive())
    followup_session = server.session_requested()
    assert followup_session.user_record is not None
    assert followup_session.user_record["username"] == username
    server.connection_lost(None)

    server2 = sshpoc.SignupSSHServer(app)
    assert server2.begin_auth(username)
    assert server2.validate_public_key(username, key)


def test_ctrl_d_closes_session(monkeypatch):
    session = sshpoc.MenuSession(object(), "tester", {"username": "tester"})
    closed = []
    original_close = session._close_io

    def wrapped_close():
        closed.append(True)
        original_close()

    monkeypatch.setattr(session, "_close_io", wrapped_close)

    class FakeChannel:
        def __init__(self):
            self.code = None

        def exit(self, code):
            self.code = code

        def close(self):
            pass

        async def wait_closed(self):
            return

        def get_terminal_size(self):
            return 80, 24

        def get_terminal_type(self):
            return "xterm"

    channel = FakeChannel()

    async def drive():
        session.connection_made(channel)
        session.data_received(sshpoc.CTRL_D, None)
        await asyncio.sleep(0)

    asyncio.run(drive())
    assert closed
    assert channel.code == 0


def fake_prompt_session():
    class Prompt:
        async def prompt_async(self, *args, **kwargs):
            raise EOFError

    return types.SimpleNamespace(prompt_async=Prompt().prompt_async, app=types.SimpleNamespace(output=None))


def fake_channel():
    class Channel:
        def __init__(self):
            self.code = None

        def exit(self, code):
            self.code = code

        def close(self):
            pass

        async def wait_closed(self):
            return

        def get_terminal_size(self):
            return 80, 24

        def get_terminal_type(self):
            return "xterm"

    return Channel()


def test_ctrl_d_exits_guest_menu(monkeypatch):
    monkeypatch.setattr(sshpoc, "print_formatted_text", lambda *args, **kwargs: None)
    session = sshpoc.MenuSession(object(), "guest", None)
    channel = fake_channel()
    session.channel = channel
    session.prompt_session = fake_prompt_session()

    async def drive():
        await session.guest_menu()

    asyncio.run(drive())
    assert channel.code == 0


def test_ctrl_d_exits_account_menu(monkeypatch):
    monkeypatch.setattr(sshpoc, "print_formatted_text", lambda *args, **kwargs: None)
    session = sshpoc.MenuSession(object(), "member", {"username": "member"})
    channel = fake_channel()
    session.channel = channel
    session.prompt_session = fake_prompt_session()

    async def drive():
        await session.account_menu()

    asyncio.run(drive())
    assert channel.code == 0


def test_data_received_strips_bracketed_paste(monkeypatch):
    session = sshpoc.MenuSession(object(), "guest", None)
    received = []
    session.pipe_input = types.SimpleNamespace(send_text=received.append)
    session.channel = fake_channel()
    session.data_received(b"\x1b[200~he", None)
    session.data_received(b"ll", None)
    session.data_received(b"o\x1b[201~", None)
    assert received == ["hello"]


def test_data_received_ctrl_d_inside_bracket(monkeypatch):
    session = sshpoc.MenuSession(object(), "guest", None)
    called = []
    monkeypatch.setattr(session, "_exit_session", lambda code=0: called.append(code))
    session.data_received(b"\x1b[200~\x04\x1b[201~", None)
    assert called == [0]


@pytest.mark.timeout(5)
def test_ctrl_d_disconnects_guest_session_real_server(app, monkeypatch):
    exits = []
    exit_event = asyncio.Event()
    original_exit = sshpoc.MenuSession._exit_session
    raw_packets = []

    original_data_received = sshpoc.MenuSession.data_received

    def track_data(self, data, datatype):
        raw_packets.append(bytes(data) if isinstance(data, (bytes, bytearray)) else data)
        return original_data_received(self, data, datatype)

    def track_exit(self, code=0):
        exits.append(code)
        if not exit_event.is_set():
            exit_event.set()
        return original_exit(self, code)

    monkeypatch.setattr(sshpoc.MenuSession, "_exit_session", track_exit)
    monkeypatch.setattr(sshpoc.MenuSession, "data_received", track_data)

    async def drive():
        server = await asyncssh.create_server(
            lambda: sshpoc.SignupSSHServer(app),
            "127.0.0.1",
            0,
            server_host_keys=app.server_keys,
        )
        try:
            host, port = server.get_addresses()[0]
            conn = await asyncssh.connect(host, port, username="guest", known_hosts=None)
            try:
                proc = await conn.create_process(term_type="xterm-256color")
                await asyncio.wait_for(proc.stdout.read(1024), timeout=1)
                proc.stdin.write(sshpoc.CTRL_D)
                await proc.stdin.drain()
                    try:
                        await asyncio.wait_for(exit_event.wait(), timeout=1)
                    except asyncio.TimeoutError:
                        return list(exits), list(raw_packets)
                    await asyncio.wait_for(proc.wait_closed(), timeout=1)
                    assert proc.exit_status == 0
                    return list(exits), list(raw_packets)
                finally:
                    conn.close()
                    await conn.wait_closed()
        finally:
            server.close()
            await server.wait_closed()

    exit_codes, packets = asyncio.run(drive())
    if exit_codes != [0]:
        raise AssertionError(f"exit codes {exit_codes!r}, packets {packets!r}")
    if not any(
        (isinstance(packet, (bytes, bytearray)) and sshpoc.CTRL_D.encode() in packet)
        or (isinstance(packet, str) and sshpoc.CTRL_D in packet)
        for packet in packets
    ):
        raise AssertionError(f"missing ctrl-d in packets {packets!r}")
