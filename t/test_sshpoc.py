import asyncssh

import sshpoc


def make_app(tmp_path):
    user_dir = tmp_path / "user"
    host_path = tmp_path / "host.json"
    return sshpoc.SignupApp(
        "127.0.0.1",
        0,
        users=sshpoc.UserStore(user_dir),
        host_keys=sshpoc.HostKeyStore(host_path),
    )


def test_session_reuses_authenticated_user(tmp_path):
    app = make_app(tmp_path)
    key = asyncssh.generate_private_key("ssh-ed25519")
    app.register_user("tester", key.export_public_key().decode())
    server = sshpoc.SignupSSHServer(app)
    assert server.begin_auth("tester")
    assert server.validate_public_key("tester", key)
    server.auth_completed()
    first = server.session_requested()
    assert first.username == "tester"
    assert first.user_record["username"] == "tester"
    second = server.session_requested()
    assert second.username == "tester"
    assert second.user_record["username"] == "tester"


def test_ctrl_d_closes_session(monkeypatch):
    session = sshpoc.MenuSession(object(), "tester", {"username": "tester"})
    closed = []
    monkeypatch.setattr(session, "_close_io", lambda: closed.append(True))

    class FakeChannel:
        def __init__(self):
            self.code = None

        def exit(self, code):
            self.code = code

    channel = FakeChannel()
    session.channel = channel
    session.data_received(sshpoc.CTRL_D, None)
    assert closed
    assert channel.code == 0
