import asyncio
import os

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
