"""
binary.py — install and locate the pinned GxTB (xtb) binary.

The binary is installed into the environment's bin/ directory when the
package is installed (via the custom setuptools install command in
setup.py).  Every subsequent call to ensure_gxtb_binary() just returns
the fixed path with no network activity.

Override with GXTB_BINARY=/path/to/xtb to skip all of this.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)

# ── pinned asset ──────────────────────────────────────────────────────────────

GXTB_TARBALL_FILENAME = "xtb-6.7.1-gxtb-140526-linux-x86_64.tar.xz"
GXTB_VERSION_TAG      = "6.7.1-gxtb-140526"
GXTB_TARBALL_URL      = (
    "https://github.com/grimme-lab/g-xtb/raw/main/binaries/"
    + GXTB_TARBALL_FILENAME
)
GXTB_SHA256_URL       = GXTB_TARBALL_URL + ".sha256"

# ── install location ──────────────────────────────────────────────────────────

def _bin_dir() -> Path:
    """bin/ directory of the Python that owns this package."""
    return Path(sys.executable).resolve().parent

def _xtb_path() -> Path:
    return _bin_dir() / "xtb"

# ── public API ────────────────────────────────────────────────────────────────

def ensure_gxtb_binary() -> Path:
    """Return path to the xtb binary. Raises if not installed."""
    env_path = os.environ.get("GXTB_BINARY")
    if env_path:
        p = Path(env_path)
        if not p.is_file():
            raise RuntimeError(
                f"GXTB_BINARY={env_path!r} does not point to a file."
            )
        return p

    xtb = _xtb_path()
    if not xtb.is_file():
        raise RuntimeError(
            f"GxTB binary not found at {xtb}.\n"
            "Re-install the package: pip install . \n"
            "Or set GXTB_BINARY=/path/to/xtb."
        )
    return xtb


def install_gxtb_binary(force: bool = False) -> Path:
    """Download and install the pinned xtb binary into the env bin/ dir.

    Called automatically during pip install.  Safe to call again with
    force=True to re-download.
    """
    xtb = _xtb_path()

    if xtb.is_file() and not force:
        print(f"GxTB binary already installed: {xtb}", flush=True)
        return xtb

    if force and xtb.exists():
        xtb.unlink()

    bin_dir = xtb.parent
    bin_dir.mkdir(parents=True, exist_ok=True)

    print(f"Installing GxTB binary ({GXTB_VERSION_TAG}) ...", flush=True)

    tmp_fd, tmp_str = tempfile.mkstemp(
        dir=bin_dir, prefix=".gxtb-", suffix=".tar.xz"
    )
    tmp = Path(tmp_str)
    try:
        os.close(tmp_fd)
        _download(GXTB_TARBALL_URL, tmp)

        sha256_tmp = tmp.parent / (tmp.name + ".sha256")
        try:
            _download(GXTB_SHA256_URL, sha256_tmp)
            expected = sha256_tmp.read_text().split()[0]
        finally:
            sha256_tmp.unlink(missing_ok=True)

        if not _verify_sha256(tmp, expected):
            raise RuntimeError(
                "SHA-256 mismatch — downloaded tarball is corrupt or the "
                "upstream asset has changed.  Set GXTB_BINARY to a local binary."
            )

        _extract_xtb(tmp, xtb)
    finally:
        tmp.unlink(missing_ok=True)

    xtb.chmod(xtb.stat().st_mode | 0o755)
    print(f"GxTB binary installed: {xtb}", flush=True)
    return xtb


def _extract_xtb(tarball: Path, dest: Path) -> None:
    with tarfile.open(tarball, "r:xz") as tf:
        member = next(
            (m for m in tf.getmembers()
             if Path(m.name).parts[-2:] == ("bin", "xtb")),
            None,
        )
        if member is None:
            raise RuntimeError(
                f"bin/xtb not found inside {tarball}.\n"
                f"Members: {[m.name for m in tf.getmembers()[:20]]}"
            )
        tmp_dest = dest.parent / f".xtb-{os.getpid()}"
        try:
            with tf.extractfile(member) as src, open(tmp_dest, "wb") as dst:
                shutil.copyfileobj(src, dst)
            tmp_dest.rename(dest)
        except Exception:
            tmp_dest.unlink(missing_ok=True)
            raise


def _download(url: str, dest: Path) -> None:
    try:
        with urllib.request.urlopen(url) as r:  # noqa: S310
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            with dest.open("wb") as fh:
                while chunk := r.read(1 << 16):
                    fh.write(chunk)
                    done += len(chunk)
                    if total:
                        print(
                            f"\r  {done/total*100:5.1f}%  "
                            f"({done>>20}/{total>>20} MiB)",
                            end="", flush=True,
                        )
        print(flush=True)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed: {exc}") from exc


def _verify_sha256(path: Path, expected: str) -> bool:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest() == expected


# ── CLI ───────────────────────────────────────────────────────────────────────

def cli_install() -> None:
    """gxtb-install — install or re-install the xtb binary."""
    import argparse
    parser = argparse.ArgumentParser(
        prog="gxtb-install",
        description=(
            "Download and install the pinned GxTB binary into this "
            "environment.  Normally called automatically during pip install."
        ),
    )
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if already installed.")
    args = parser.parse_args()
    install_gxtb_binary(force=args.force)


if __name__ == "__main__":
    cli_install()
