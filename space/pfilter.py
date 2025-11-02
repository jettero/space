#!/usr/bin/env python
# coding: utf-8


def adj_map(**kw):
    kw = {k: (v if isinstance(v, (list, tuple)) else (v,)) for k, v in kw.items()}

    def decorator(f):
        f.adj_map = kw
        return f

    return decorator
