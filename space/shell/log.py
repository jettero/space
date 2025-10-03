# coding: utf-8

import logging
from .base import BaseShell

log = logging.getLogger(__name__)


class Shell(BaseShell):
    def receive_message(self, msg):
        msg = msg.render_text(color=False).splitlines()
        msg = "\n  " + "\n  ".join(msg)
        log.info("%s heard: %s", self, msg)
