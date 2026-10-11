#!/usr/bin/env python3
"""Build a reproducible installable addon ZIP without development/reference files."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADDON = "LegacyAchievementsReforged"


def package(output_dir, root=ROOT):
    addon = Path(root) / ADDON
    toc = addon / (ADDON + ".toc")
    text = toc.read_text(encoding="utf-8")
    match = re.search(r"^## Version: ([\w.-]+)$", text, re.M)
    if not match:
        raise ValueError("TOC must declare a valid release version")
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not (addon / line.replace("\\", "/")).is_file():
            raise ValueError("Missing TOC file: " + line)
    for path in addon.rglob("*.xml"):
        for element in ET.parse(path).iter():
            if element.tag.rsplit("}", 1)[-1] in ("Script", "Include") and "file" in element.attrib:
                if not (path.parent / element.attrib["file"].replace("\\", "/")).is_file():
                    raise ValueError("Missing XML dependency in " + str(path))
    allowed = {".lua", ".toc", ".xml", ".tga", ".wav", ".ogg", ".md"}
    files = sorted(p for p in addon.rglob("*") if p.is_file() and p.suffix.lower() in allowed)
    if any(p.is_symlink() for p in files):
        raise ValueError("Addon release files must not be symlinks")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / (ADDON + "-" + match[1] + ".zip")
    checksum = archive.with_suffix(".zip.sha256")
    if archive.exists() or checksum.exists():
        raise FileExistsError("Release already exists; choose another output directory")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            name = ADDON + "/" + path.relative_to(addon).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("Release ZIP failed integrity check")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with checksum.open("x", encoding="utf-8") as f:
        f.write(digest + "  " + archive.name + "\n")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".release")
    args = parser.parse_args()
    try:
        archive = package(args.output_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")
    print(archive)


if __name__ == "__main__":
    main()
