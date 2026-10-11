#!/usr/bin/env python3
"""Copy an earlier addon's account/character saves into the renamed addon.

Close WoW first. Preview is the default; --apply creates new files. Source files
are never executed, edited or deleted. Existing different target saves abort the
whole plan so a newer character/account cannot be overwritten accidentally.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
import re

TARGET_ADDON = "LegacyAchievementsReforged"


@dataclass(frozen=True)
class SaveCopy:
    source: Path
    target: Path
    contents: bytes


def migration_plan(wtf_root, source_addon):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", source_addon) or source_addon == TARGET_ADDON:
        raise ValueError("Source addon must be the previous folder's identifier")
    wtf = Path(wtf_root).resolve()
    if not wtf.is_dir():
        raise ValueError("WTF folder does not exist")
    plan = []
    for source in sorted(wtf.rglob(source_addon + ".lua")):
        if source.parent.name != "SavedVariables":
            continue
        if source.is_symlink() or any(p.is_symlink() for p in source.relative_to(wtf).parents if (wtf / p).exists()):
            raise ValueError("Save paths must not be symlinks: " + str(source))
        contents = source.read_bytes()
        found = False
        for suffix in ("DB", "CharDB"):
            old = (source_addon + suffix).encode("ascii")
            new = (TARGET_ADDON + suffix).encode("ascii")
            # Change only serialized top-level assignments, never strings,
            # comments, nested keys, timestamps, counters or attribution data.
            pattern = rb"(?m)^(\xef\xbb\xbf)?" + re.escape(old) + rb"(?=[ \t]*=)"
            contents, changed = re.subn(pattern, lambda m: (m[1] or b"") + new, contents)
            found = found or changed > 0
        if not found:
            raise ValueError("No supported saved table assignments in " + str(source))
        target = source.with_name(TARGET_ADDON + ".lua")
        if target.is_symlink():
            raise ValueError("Target save must not be a symlink: " + str(target))
        if target.exists():
            if target.read_bytes() != contents:
                raise ValueError("Existing target save differs; nothing copied: " + str(target))
            continue  # An identical prior migration is safe to repeat.
        plan.append(SaveCopy(source, target, contents))
    if not plan and not any(p.parent.name == "SavedVariables" for p in wtf.rglob(source_addon + ".lua")):
        raise ValueError("No source saves found; verify WTF path and source addon name")
    return plan


def apply_plan(plan):
    # Validate every destination before starting, then use exclusive creation
    # to guard against a race or a target created after the preview.
    if any(item.target.exists() or item.target.is_symlink() for item in plan):
        raise FileExistsError("A target save appeared after planning; nothing copied")
    created = []
    try:
        for item in plan:
            with item.target.open("xb") as f:
                created.append(item.target)
                f.write(item.contents)
    except BaseException:
        # Roll back only this invocation's new copies; keep every source save.
        for target in created:
            target.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wtf-root", type=Path, required=True)
    parser.add_argument("--source-addon", required=True, help="Previous addon folder basename")
    parser.add_argument("--apply", action="store_true", help="Create new saves after previewing with WoW closed")
    args = parser.parse_args()
    try:
        plan = migration_plan(args.wtf_root, args.source_addon)
        for item in plan:
            print(str(item.source) + " -> " + str(item.target))
        if args.apply:
            apply_plan(plan)
        print(str(len(plan)) + (" saves copied. Originals retained." if args.apply else " saves planned. Run with --apply to copy."))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
