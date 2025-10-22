HARD CONSTRAINTS

- No comments in code unless explicitly allowed
  - don't remove comments I put there unless they're nolonger true because of
    the code changes
  - definitely don't add any that say what the next line of code does when the
    next line of code very obviously already does that
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

These constraints apply to all changes within this repository unless a task explicitly grants exceptions.
