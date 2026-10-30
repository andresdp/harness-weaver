"""Build a deterministic Overleaf import ZIP from the current paper sources."""

from __future__ import print_function

import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "HarnessWeaver-CAIN-2027-Overleaf.zip"
SOURCE_FILES = (
    HERE / "main.tex",
    HERE / "references.bib",
)
PACKAGE_README = HERE / "OVERLEAF.md"


def add_bytes(archive, name, content):
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def main():
    missing = [str(path) for path in SOURCE_FILES + (PACKAGE_README,) if not path.is_file()]
    if missing:
        raise SystemExit("Missing paper package input(s):\n" + "\n".join(missing))

    buffer = io.BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in SOURCE_FILES:
            add_bytes(archive, path.name, path.read_bytes())
        add_bytes(archive, "README.md", PACKAGE_README.read_bytes())

    content = buffer.getvalue()
    if not ARCHIVE.exists() or ARCHIVE.read_bytes() != content:
        ARCHIVE.write_bytes(content)
        print("Updated {}".format(ARCHIVE))
    else:
        print("Already up to date: {}".format(ARCHIVE))


if __name__ == "__main__":
    main()
