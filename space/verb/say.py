#!/usr/bin/env python
# coding: utf-8

from .base import Verb


class Action(Verb):
    name = "say"

    def do_say_words(self, words):
        text = words.strip()
        style = None
        suffixes = {
            ":)": ("happily $vdeclare", 2),
            "=(": ("sadly $vmumble", 2),
            ";)": ("$vwink and $vsuggest", 2),
            ":(": ("sadly $vmumble", 2),
            ":0": ("$vlook shocked and $vsay", 2),
            ":|": ("sullenly $vstate", 2),
            ":/": ("$vsmirk and $vsay", 2),
            ":P": ("$vstick out $p tongue and $vsay", 2),
            ":p": ("$vstick out $p tongue and $vsay", 2),
            "=)": ("$vsmile brightly and $vsay", 2),
            "=<": ("sarcastically $vstate", 2),
            "=>": ("facetiously $vsay", 2),
            "\\o/": ("$vthrow $p hands in the air and $vshout", 3),
        }
        for suf, (templ, n) in sorted(suffixes.items(), key=lambda kv: -len(kv[0])):
            if text.endswith(suf):
                style = templ
                text = text[:-n]
                break

        verb = None
        if style is None:
            if text.endswith("!"):
                verb = "exclaim"
            elif text.endswith("?"):
                verb = "ask"

        if text:
            core = text
            core = core.rstrip()
            if core.startswith("(") and core.endswith(")") and len(core) >= 2:
                inner = core[1:-1].strip()
                self.simple_action('$N $vinterject parenthetically, "$O"', inner)
                return
            if verb is None:
                if core and core[-1] not in ".!?":
                    core += "."
            else:
                if core and core[-1] not in ".!?":
                    core += "!" if verb == "exclaim" else "?"
            text = core

        if style is not None:
            self.simple_action(f'$N {style}, "$O"', text)
        else:
            v = verb or "say"
            self.simple_action(f'$N $v{v}, "$O"', text)
