"""
Generate emote verbs from the MudOS soul data.

Parser/router wiring is intentionally deferred. We keep the verbs ready for
later integration where the router can ask the verb itself for can_/do_ logic.
"""

import re
import logging
import random
from collections import namedtuple

from space.verb.emote.soul import SOUL
from space.verb.base import Verb
from space.living.base import Living
from space.stdobj import StdObj

log = logging.getLogger(__name__)

BLESSED_TOKENS = {
    "LIV": ("liv", "{aname}:Living"),
    "OBJ": ("obj", "{aname}:StdObj"),
    "WRD": ("word", "{aname}:str"),
    "STR": ("words", "{aname}:tuple[str,...]"),
}

SAFE_TOKEN = re.compile(r"^[a-zA-Z][A-Za-z0-9-]+$")
EmoteInfo = namedtuple("EmoteInfo", 'sig template vars args wrd_vals'.split())

def compute_db(name, patterns):
    ret = dict()

    xlate_templates = {sig:template for sig,template in patterns.items()}
    for sig, template in patterns.items():
        if isinstance(template, list):
            template = [ (xlate_templates[item[1:]] if item.startswith('=') else item) for item in template ]
        elif template.startswith('='):
            template = xlate_templates[template[1:]]
        tokens = [x for x in sig.split(" ") if x]
        fn_name = [name.replace("-", "_")]
        vars = list()
        args = list()
        wrd_vals = dict()
        counts = dict()
        for token in tokens:
            try:
                aname, afmt = BLESSED_TOKENS[token]
            except KeyError:
                aname, afmt = BLESSED_TOKENS["WRD"]
                if not SAFE_TOKEN.match(token):
                    raise ValueError(f'"{token}" is not a good token for an emote syntax key')
                if aname not in wrd_vals:
                    wrd_vals = {aname: {token: template}}
                else:
                    wrd_vals[aname][token] = template
            try:
                aname = f"{aname}{counts[aname]}"
                counts[aname] += 1
            except KeyError:
                counts[aname] = 1
            vars.append(aname)
            args.append(afmt.format(aname=aname))
            fn_name.append(aname)
        #########################################
        fn_name = "_".join(fn_name)
        if fn_name not in ret:
            ret[fn_name] = EmoteInfo(sig=sig, template=template, vars=vars, args=args, wrd_vals=wrd_vals)
        for aname,wv in wrd_vals.items():
            ret[fn_name].wrd_vals[aname].update(wv)
    return ret

class Emote(Verb):
    def __init__(self, name, patterns):
        if not SAFE_TOKEN.match(name):
            raise ValueError(f'"{name}" is not a good name for an emote')
        self.name = name
        self.rule_db = compute_db(name, patterns)
        #for fn_name, rule_db_ent in self.rule_db.items():
            #self.generate_can_fn(fn_name, rule_db_ent)
        super().__init__()

    def generate_can_fn(self, fn_name, ent, on_cls=Living, src_only=False):
        fn_name = f"can_{fn_name}"
        fn_args = ", ".join(ent.args)
        fn_vars = ", ".join( f'"{x}":{x}' for x in ent.vars )

        source_code = [ f"def {fn_name}(self, {fn_args}):" ]

        if ent.wrd_vals:
            for wrd,vals in ent.wrd_vals.items():
                tv = tuple(vals)
                source_code.append(f"  if {wrd} not in {tv!r}:")
                source_code.append(f"    return {{'error': f'\"{{{wrd}}}\" not understood'}}")
            source_code.append(f"  template = ent.word_vals[\"{wrd}\"][{wrd}]")
        elif isinstance(ent.template, (tuple,list)):
            source_code.append(f'  template = random.choice({ent.template!r})')
        else:
            source_code.append(f'  template = {ent.template!r}')

        source_code.append(f'  return True, {{ {fn_vars}, "template":template }}')
        source_code = "\n".join(source_code) + '\n'

        if src_only:
            return source_code

        ns = dict(Living=Living, StdObj=StdObj)
        exec(source_code, ns)
        setattr(on_cls, fn_name, ns[fn_name])

    def generate_do_fn(self, sig, template, on_cls=Living):
        pass


EMOTES = {e.name: e for e in [Emote(name=name, patterns=patterns) for name, patterns in SOUL["emotes"].items()]}
