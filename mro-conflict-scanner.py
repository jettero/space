#!/usr/bin/env python3
# coding: utf-8

"""
Scan the project for MRO attribute conflicts.

Finds attributes (methods/properties/descriptors/data descriptors) that are
defined by 2+ direct bases of a class and are not overridden in the subclass
itself. This often indicates an ambiguous selection where MRO order decides
which wins silently.

Usage:
  python mro-conflict-scanner.py [package [package ...]]

Defaults to scanning the top-level "space" package.
"""

import argparse
import importlib
import inspect
import os
import pkgutil
import sys
import subprocess
from types import ModuleType
from typing import Dict, Iterable, List, Set, Tuple


def iter_modules_in_package(pkg_name: str) -> Iterable[str]:
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:  # pragma: no cover - best effort import
        return []
    if not hasattr(pkg, "__path__"):
        return []
    for m in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        yield m.name


def import_safely(mod_name: str) -> ModuleType:
    try:
        return importlib.import_module(mod_name)
    except Exception:
        return None  # best effort; skip modules that fail to import


def is_descriptor(obj) -> bool:
    return (
        hasattr(obj, "__get__")
        or hasattr(obj, "__set__")
        or hasattr(obj, "__delete__")
    )


def classify_attr(obj) -> str:
    if inspect.isfunction(obj) or inspect.ismethoddescriptor(obj):
        return "function"
    if isinstance(obj, property):
        return "property"
    if is_descriptor(obj):
        return "descriptor"
    return "data"


def direct_defined_attributes(cls: type) -> Set[str]:
    # Exclude dunder attributes except a few important ones we care about
    allowed_dunders = {"__str__", "__repr__", "__format__", "__iter__"}
    attrs = set()
    for name in cls.__dict__.keys():
        if name.startswith("__") and name.endswith("__") and name not in allowed_dunders:
            continue
        attrs.add(name)
    return attrs


def collect_base_definitions(cls: type) -> Dict[str, List[Tuple[type, object]]]:
    """Collect concrete definitions for each direct base and its MRO below cls.

    For each direct base B of cls, walk B.__mro__ up to but not including cls,
    and record the first class in that chain that defines an attribute name
    (i.e., has it in its __dict__). This way we catch cases where two direct
    bases inherit the same attribute from a shared ancestor (e.g., baseobj).
    """
    # Map attribute name -> list of (direct_base, defining_class, object)
    defs: Dict[str, List[Tuple[type, type, object]]] = {}
    for base in cls.__bases__:
        # Build the slice of MRO from base up to (but excluding) cls
        chain = []
        for c in base.__mro__:
            if c is cls:
                break
            chain.append(c)
        # For each name, capture the first defining class in this chain
        first_def: Dict[str, Tuple[type, object]] = {}
        for c in chain:
            for name, obj in c.__dict__.items():
                if name not in first_def:
                    first_def[name] = (c, obj)
        for name, (definer, obj) in first_def.items():
            defs.setdefault(name, []).append((base, definer, obj))
    return defs


def find_conflicts_in_class(cls: type) -> List[Tuple[str, List[Tuple[type, type, object]]]]:
    if not cls.__bases__:
        return []
    own = set(cls.__dict__.keys())
    base_defs = collect_base_definitions(cls)
    conflicts: List[Tuple[str, List[Tuple[type, type, object]]]] = []

    for name, entries in base_defs.items():
        # If subclass defines the attribute, we consider the conflict resolved.
        if name in own:
            continue
        # Ignore names that ultimately resolve from the same defining class
        # across all bases (i.e., multiple bases inherit the same definition
        # from a single ancestor). Those are not true conflicts.
        defining_classes = set(definer for _, definer, _ in entries)
        if len(defining_classes) == 1:
            continue
        # Consider only attributes present in 2+ distinct bases
        bases_with = {}
        for base, definer, obj in entries:
            bases_with.setdefault(base, (definer, obj))
        if len(bases_with) < 2:
            continue

        # Skip common harmless or irrelevant names, including those provided only by object
        if name in {"__module__", "__doc__", "__weakref__", "__dict__"}:
            continue
        # Exclude if all contributing definitions are ultimately from built-in object.
        # If any comes from object, we still include only if at least one other
        # comes from a non-object class (i.e., a real overlap within code).
        contributing_classes = [definer for _, definer, _ in entries]
        if all(c is object for c in contributing_classes):
            continue

        # At this point, we have 2+ direct bases that would supply a definition
        # for the same name (possibly via their own ancestors). That's a conflict.
        # Only consider duplicates where 2+ distinct direct bases contribute
        # different defining classes.
        conflicts.append((name, [(b, d, o) for b, (d, o) in bases_with.items()]))

    return conflicts


def scan_packages(pkgs: Iterable[str]) -> List[Tuple[type, List[Tuple[str, List[Tuple[type, object]]]]]]:
    classes: List[type] = []
    for pkg in pkgs:
        # include the package module itself
        for mod_name in [pkg, *iter_modules_in_package(pkg)]:
            mod = import_safely(mod_name)
            if not mod:
                continue
            for _, obj in vars(mod).items():
                if inspect.isclass(obj) and obj.__module__ == mod.__name__:
                    classes.append(obj)
    # Deduplicate classes
    seen = set()
    uniq = []
    for c in classes:
        k = (c.__module__, c.__qualname__)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)

    results = []
    for cls in uniq:
        confs = find_conflicts_in_class(cls)
        if confs:
            results.append((cls, confs))
    return results


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Scan for MRO conflicts")
    parser.add_argument("packages", nargs="*", default=["space"], help="Packages to scan")
    parser.add_argument(
        "-f",
        "--function",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob to match function names; repeatable. Example: -f '__*' -f 'do_*'",
    )
    parser.add_argument(
        "-F",
        "--ignore-function",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob to exclude function/attribute names; repeatable.",
    )
    parser.add_argument(
        "-o",
        "--object",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob to include class names (module.qualname); repeatable.",
    )
    parser.add_argument(
        "-O",
        "--ignore-object",
        action="append",
        default=[],
        metavar="GLOB",
        help="Glob to exclude class names (module.qualname); repeatable.",
    )
    args = parser.parse_args(argv)

    # Add CWD to sys.path to import the package in editable mode
    sys.path.insert(0, os.getcwd())

    results = scan_packages(args.packages)
    if not results:
        print("No potential MRO conflicts found.")
        return 0

    # Prepare rows for a tabular display
    rows: List[Tuple[str, str, str, str]] = []
    import fnmatch
    for cls, confs in sorted(results, key=lambda x: (x[0].__module__, x[0].__qualname__)):
        cls_name = f"{cls.__module__}.{cls.__qualname__}"
        if args.object and not any(fnmatch.fnmatch(cls_name, pat) for pat in args.object):
            continue
        if args.ignore_object and any(fnmatch.fnmatch(cls_name, pat) for pat in args.ignore_object):
            continue
        bases = ", ".join(b.__name__ for b in cls.__bases__)
        for name, entries in sorted(confs, key=lambda x: x[0]):
            # If function filters provided, require the attribute name to match any glob
            if args.function and not any(fnmatch.fnmatch(name, pat) for pat in args.function):
                continue
            if args.ignore_function and any(fnmatch.fnmatch(name, pat) for pat in args.ignore_function):
                continue
            # Split entries into aligned columns per base, including via path
            # Show as Base->Definer:type when definer differs from Base.
            srcs = []
            for base, definer, obj in entries:
                kind = classify_attr(obj)
                if definer is base:
                    srcs.append(f"{base.__name__}:{kind}")
                else:
                    srcs.append(f"{base.__name__}->{definer.__name__}:{kind}")

            # Which definer wins by actual MRO resolution for this class?
            # Look up attribute along cls.__mro__ and record the class that defines it.
            winner_cls = None
            for c in cls.__mro__:
                if name in getattr(c, "__dict__", {}):
                    winner_cls = c
                    break
            # Merge winner into Attribute column as Winner.attr
            if winner_cls:
                attr_disp = f"{winner_cls.__name__}.{name}"
            else:
                attr_disp = name

            rows.append((cls_name, bases, attr_disp, ", ".join(srcs)))

    # Compute column widths
    headers = ("Class", "Bases", "Attribute (winner)", "Defined In (base:type)")
    # Order rows by function/attribute name, then by winner class name, then by class/module
    def sort_key(r):
        # r[2] is Attribute (winner) like 'Winner.attr' or just 'attr'
        attr = r[2]
        if '.' in attr:
            winner, fname = attr.split('.', 1)
        else:
            winner, fname = "", attr
        return (fname, winner, r[0])

    rows.sort(key=sort_key)

    cols = list(zip(*([headers] + rows))) if rows else [headers]
    widths = [max(len(str(cell)) for cell in col) for col in cols]

    def fmt_row(r):
        return "  ".join(str(v).ljust(w) for v, w in zip(r, widths))

    output_lines = []
    output_lines.append(fmt_row(headers))
    output_lines.append("  ".join("-" * w for w in widths))
    if not rows:
        output_lines.append(fmt_row(("<none>", "", "", "")))
    else:
        for r in rows:
            output_lines.append(fmt_row(r))

    text = "\n".join(output_lines) + "\n"

    pager = os.environ.get("PAGER")
    if pager:
        try:
            # Close stdout and reopen to pager by launching pager and writing to its stdin
            with subprocess.Popen(pager, shell=True, stdin=subprocess.PIPE) as proc:
                proc.stdin.write(text.encode("utf-8", errors="replace"))
                proc.stdin.close()
                proc.wait()
            return 0
        except Exception:
            # Fallback to printing directly if pager fails
            pass
    sys.stdout.write(text)

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
