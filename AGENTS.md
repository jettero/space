# TRICKS
- you can use `./lrun-shell.py < /dev/null` to do a kind of trivial space.shell.prompt test
- always: if you write new tests, run those before running the full test suite
- always: if you know certain tests are relevant to the code you modified, always run those tests before the full test suite
- use your tools:
    - use `kagi_fastgpt` if you need to search for examples or docs
    - use `kagi_summarize` if you want to check the contents of a specific URL
    - use `kagi_search` if you just want to quickly search for something
- you can't run `lrun-shell.py` in any way because you cannot allocate a PTY
- you should use `black -l 127` as a basic syntax check. I have to run that anyway due to pre-commit constraint.
- before using introspection to figure out `prompt_toolkit` syntax, please scan the reference doc in `contrib/pt_doc.html`

# HARD CONSTRAINTS
- always tell me when you read this file (so I know for sure you see it on startup)
- shorter is better and easier to read. don't spend 40 lines doing what you could do in 5
- use the walrus operator (`if m := something`)
- do not re-invent the wheel. Use the tools and built-in helpers from the libraries you're using
- don't repeat yourself. DRY everything you can
- always be very brief with your words. If you resort to bullet points, make sure they don't repeat the same thing over and over.
- Don't resort to words when code would explain better. The most concise language we have for talking about code is the code itself. I can read it.
- default to public names. Mostly little helper functions do not need to be
  private. Avoid `_private_name` unless whatever private name seems really to be 100% compeltely internal-use only
- Do not add comments to the code unless explicitly told to do so
  - don't remove comments I put there unless they're nolonger true because of
    the code changes
  - use expressive code that tells the story without the need for comments
  - you don't understand when to use comments, so just don't use them
- Do not use getattr/hasattr unless explicitly allowed
- stop doublechecking every fucking little thing when you already carefully
  checked the type. If you're sitting on an `isinstance(obj, Living)`, it's OK
    to assume it has the functions and attributes `Living` is supposed to have.
- Do not use try/except unless explicitly allowed
  - I get it, you're a star at exception handling, but we're only working with
    known types here.
  - Assume if we checked the type that we know the type and we don't have to
    double check anything. If we're in a logging filter
    ```
    class STFU(logging.Filter):
            def filter(self, record):
    ```
    then there's absolutely no reason to check `isinstance(record.msg, str)` we
    already fucking know it's a string. it's a logging message?!?
- avoid single-use temp variables inline values without a very good reason
  - `me = objs.me` is never going to be ok, stop doing it
  - `objs = me.map.locaion.visicalc(...)` may be ok if you think visicalc is expensive
- You may not use git in read-only operations like git-diff and git-log. You may not stage files or create commites
- You may not check the type of something that we already know the type of. I
  have no idea why you chose to do it, but in the following code:
    ```
    logging.basicConfig(level=logging.DEBUG)
    for h in logging.root.handlers:
        h.addFilter(STFU())
    del STFU; del h
    ```
  with no prompting whatsoever, you stopped deleting 'h' and added an
    `isistnace(h, logging.StreamHandler)` when we already know for 100% sure the
  items in logging.root.handlers are absolutely stream handlers.
- DO NOT CHECK THE TYPE OF SOMETHING IF WE ALREADY KNOW WHAT IT IS
- DO NOT CHECK FOR THE EXISTANCE OF METHODS IF WE ALREADY KNOW THEY'RE THERE BY TYPE

## Avoid
- avoid changes to fundemental building blocks like parser.py args.py and router.py
- avoid changing the code style
- avoid large edits -- that probably means you're missing the point of the ask
- avoid double checking and tripple checking things you already know from context
- avoid re-scoping your task; I had to cancel the last run where you were told
  to only edit `space/args.py` and you modified over 20 files you were not
  instructed to edit. These changes just end up getting reversed.

## Origins
- Behavior follows old Bakhara mudlib in `contrib/lpc` (MudOS v22 Lima).
- Port ideas, not LPC APIs. Stay Pythonic.
- For names, see `contrib/lpc/std/object/names.c`; for messages, see `contrib/lpc/std/modules/m_messages.c`.
- never modify files in `contrib/`, `.git/`

## Always
- when creating tests, always work with what you have. don't re-invent the wheel
- when running pytest, always run pytest directly don't bother with Makefiles
- if you fail a test, be sure to always check `last-test-run.log` for hints
  about the failure.
- Do not try to append the `last-test-run.log` on your own, pytest itself sets up the logfile for you by default.
- always stop and ask for permission when you start re-scoping your edits. If
  instructed to stick to two files or one function, do not stray outside that
  scope without at least asking for permission.

## Imports
- Place all imports at the top of the file.
- Order: standard library/builtins, third‑party, then local/space imports.
- Only break this rule to avoid circular import issues.

## Layout
- Code: `space/` • Tests: `t/` • Config: `Makefile`, `pytest.ini`, `.pre-commit-config.yaml`, `pylintrc`.
- Artifacts: `build/`, `dist/`, `space.egg-info/`.
- Reqs: `requirements.txt` (run), `test-requirements.txt` (dev/test).

## gotchas
- space.obj.strongify() exists to look-for and eliminate a Heisenbug. It shouldn't really ever be necessary to use it.
- if I type a vim command by accdident, ignore it. Examples: `ZZy`, `:q`, `:q!`, `:wq`, `:wq!`; sometimes I'm just in the wrong window

## Single-use Variables (Agent Only)
- You (the agent) must not introduce single-use temporary variables.
  This is a horrible pattern. 'v' has literally no purpose. stop doing this.
  ```
  @goom.setter
  def goom(self, v):
    v = something_dumb(v)
    self._goom = v
  ```
- You must inline values that are used exactly once.
- You must not create an intermediate solely to pass to one call.
- You must not add throwaway names like `tmp`, `code`, or `filename` used once.
- You must compose expressions instead of staging them in one-off temps.
- You must prefer direct calls with computed arguments over pre-binding.
- You must not create locals solely for a single return/exec.
- You must pass computed values directly into their consumer.
- You must avoid ephemeral placeholders such as `res`, `out`, `buf` when single-use.
- You must collapse trivial variables into the consuming expression.
- You must keep scope clean by not adding one-shot names.
- You must not remove single-use variables written by humans.
- You must only remove single-use temps that you introduced.

## Function Documentation
- Write docstrings as short documents that plainly state what the function does; include inputs and key behaviors instead of vague summaries.
- Wrap lines around 70–80 characters so the devs can read it -- document generators reflow these comments anyway
- Close/open docstring triple quotes on their own line and leave a blank line between the docstring and the function body.
- Use multi-paragraph docstrings when needed; keep them concise but cover important semantics like scoring, filtering, or other side effects.
- annotate documented functions, since that's a very useful part of the documentation
- avoid the @overload/... syntax if there's variable calling signatures, choose the single-pipe OR syntax for these cases
