# coding: utf-8

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from .base import BaseShell, IntentionalQuit

# This is supposed to behave more or less like a readline shell, but with async
# events streaming in and better tab completion.
#
# We have to be very careful here to not re-invent the wheel. prompt-toolkit
# has a lot of built in functionality and options that we should try to use
# before hand-rolling our own stupid shitware.
#
# However, we want to make sure of the following things:
#
#########  Shell Behavior
# 0. EOF and ^D, should exit the shell cleanly.
# 1. SIGINT and SIGTERM should exit the shell cleanly and tell the user
#    "received interrupt signal. see ya" or some such
# 2. The prompt should be allowed to reach the bottom of the terminal window.
#    This is worth mentioning in prompt-toolkit because by default it tries to
#    reserve room for a floating menu and we end up with 3-5 blank lines at the
#    bottom of the terminal window that are never used for anything. ick.
# 3. the main exception to the prompt at the end of the window would be if the
#    user input wraps at the right edge of the terminal; in which case we,
#    should certainly let the prompt move up a line so we can see all the
#    input.
#
#########  Tab Completion
# With respect to completion, the following should also always be true. Assume
# all available tokens for the below assertion are `['override', 'overflow',
# 'overwhelm', 'open', 'smile', 'smirk', 'grin']`
#
# 0. we should be trying to mimic the default completion modes of
#    readline/bash, prompt toolkit wants to do the cycle-through-choices thing
#    by default and it's awful and horrible and we don't want that by default
#    -- although we may add it as a configurable option later
# 1. tab completion should never add characters the user didn't type (besides
#    possibly a space after a full completion)
# 2. never guess for the user if the choice is ambiguous
# 3. if the input is empty and the user issues a '<tab>', nothing should happen
#    since the choice is totally ambiguous and the user typed 'o<tab>'
# 4. if the input is empty (called e-in from now on), 'o<tab>' should still not
#    do anything since we can't guess if the user wants a 'v' or a 'p' or an
#    'm' next.
# 5. however, if we add a 'v' so we're at 'ov' and type a '<tab>' it can and
#    should complete to 'over'
# 6. at e-in if we type 'over<tab>' or if we simply type a '<tab>' after it
#    completes to 'over', nothing should happen since we can't know if they
#    (the user) mean to go with 'w' or 'r' or 'f' next.
#
#########  Choice Display
# 0. in the above scenarios if we ever type '<tab><tab>' without any edits
#    between them -- and to be clear, that's a single '<tab>' followed by
#    another '<tab>' without typing any letters, spaces, arrows, backspaces or
#    any other characters/codes in between; we should (only in this case)
#    display a list of available completions.
# 1. ideally, the list of choices should be some kind of pop-up menu we can use
#    the arrow keys to navigate, but it should update when we type something.
# 2. if it pops up above the prompt, the lower left corner should align with
#    the typed text
# 3. and if it obscures any text, that text should be restored when the menu
#    goes away or shrinks in size
# 4. we would prefer said menu to pop up above the prompt line so we don't have
#    to move the pump up from the bottom of the terminal window
# 5. prompt-toolkit does have built in mechanisms for floating-menu popups
#    relating to tab completion, but by default the spawn below the prompt,
#    which messes up our goal of keeping the prompt as close to the bottom of
#    the screen as possible.


class Shell(BaseShell):
    color = True

    def startup(self, init=None):
        self._session = PromptSession()
        self._patch = patch_stdout(raw=True)
        self._patch.__enter__()
        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def receive_message(self, msg):
        print(msg.render_text(color=self.color))

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def internal_command(self, line):
        if line.startswith("/"):
            if line.strip() in ("/quit", "/exit"):
                self.stop()
            return True

    def step(self):
        try:
            line = self._session.prompt("/space/ ").strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()

    def get_std_tokens():
        """
        tokens to complete words prefixed with '$'
        if the tokens are (e.g.) `["useless", "bauble"]`, `"$us"` could complete to `"useless"`
        """
        return sorted({t for o in self.owner.nearby_objects for t in o.tokens})

    def get_living_tokens():
        """
        tokens to complete words prefixed with '@'
        if the tokens are (e.g.) `["stupid", "skellyman"]`, `"@st"` could complete to `"stupid"`
        """
        return sorted({t for o in self.owner.nearby_livings for t in o.tokens})
