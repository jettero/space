#!/usr/bin/env python
# coding: utf-8
# source: https://eli.thegreenplace.net/2016/basics-of-using-the-readline-library/#Python

import readline

def make_completer(vocabulary):
    def custom_complete(text, state):
        # None is returned for the end of the completion session.
        results = [x for x in vocabulary if x.startswith(text)] + [None]
        # A space is added to the completion since the Python readline doesn't
        # do this on its own. When a word is fully completed we want to mimic
        # the default readline library behavior of adding a space after it.
        return results[state] + " "
    return custom_complete

def main():
    vocabulary = {'cat', 'dog', 'canary', 'cow', 'hamster'}
    readline.parse_and_bind('tab: complete')
    readline.set_completer(make_completer(vocabulary))

    print(f"tab complete in: {vocabulary}")

    try:
        while True:
            s = input('>> ').strip()
            print('[{0}]'.format(s))
    except (EOFError, KeyboardInterrupt) as e:
        print('\nShutting down...')

if __name__ == '__main__':
    main()
