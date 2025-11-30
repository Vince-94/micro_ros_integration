#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------
"""
Optimized flash helper for RP2040 / UF2 / picotool / openocd.

Usage:
  ./scripts/flash.py -p rp2040
  ./scripts/flash.py -p rp2040 --method picotool
  ./scripts/flash.py -p rp2040 --uf2 /full/path/firmware.uf2 --wait 10
"""
from __future__ import annotations
import json
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import getpass
import click
import yaml
import os

# ---------- helpers ----------
def echo_err(msg: str) -> None:
    """Emit an error line (no exit)."""
    click.echo(f"[error] {msg}", err=True)

def run_cmd(cmd: List[str] | str, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> bool:
    """Run a command. Return True on success, False on failure."""
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = cmd
    # pretty print
    try:
        pretty = shlex.join(args) if isinstance(args, list) else str(args)
    except Exception:
        pretty = " ".join(args)
    click.echo("+ " + pretty)
    try:
        subprocess.run(args, cwd=str(cwd) if cwd else None, env=env, check=True)
        return True
    except subprocess.CalledProcessError as e:
        echo_err(f"Command failed (rc={e.returncode}): {' '.join(args)}")
        return False
    except FileNotFoundError:
        echo_err(f"Command not found: {args[0]}")
        return False

def abspath_from_manifest(manifest_path: Path, value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    p = Path(value)
    if p.is_absolute():
        return p
    return (manifest_path.parent / p).resolve()

# ---------- manifest ----------
def load_manifest(platform: str) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    """
    Return (manifest, manifest_path) on success, (None, None) on failure.
    Caller must handle error reporting.
    """
    manifest_path = Path("platforms") / platform / "platform.yaml"
    if not manifest_path.exists():
        echo_err(f"Platform manifest not found: {manifest_path}")
        return None, None
    try:
        with manifest_path.open("r") as fh:
            manifest = yaml.safe_load(fh) or {}
        return manifest, manifest_path
    except Exception as e:
        echo_err(f"Failed to load manifest {manifest_path}: {e}")
        return None, None

# ---------- UF2 mount detection ----------
def _common_mount_paths(label: str) -> List[Path]:
    user = getpass.getuser() or ""
    out: List[Path] = []
    # common desktop mounts
    out.extend([
        Path("/run/media") / user / label,
        Path("/media") / user / label,
        Path("/media") / label,
        Path("/Volumes") / label,   # macOS
        Path("/mnt") / label,
    ])
    return out

def find_rpi_rp2_mount(label: str = "RP2350") -> Optional[Path]:
    """Try many heuristics to find a mounted RP2350 mass-storage device."""
    # 1) quick check common locations
    for p in _common_mount_paths(label):
        if p.exists():
            return p

    # 2) use lsblk -J on Linux to find mountpoint with matching label
    if shutil.which("lsblk") and sys.platform.startswith("linux"):
        try:
            out = subprocess.check_output(["lsblk", "-J", "-o", "NAME,LABEL,MOUNTPOINT,TYPE"], text=True)
            data = json.loads(out)
            # recursive search
            def search(nodes):
                for n in nodes:
                    label_val = n.get("label") or n.get("LABEL") or ""
                    mnt = n.get("mountpoint") or n.get("MOUNTPOINT") or ""
                    if label in label_val and mnt:
                        return Path(mnt)
                    if n.get("children"):
                        r = search(n["children"])
                        if r:
                            return r
                return None
            r = search(data.get("blockdevices", []))
            if r:
                return r
        except Exception:
            pass

    # 3) /dev/disk/by-label -> find device and map it with findmnt
    bylabel = Path("/dev/disk/by-label")
    if bylabel.exists():
        target = bylabel / label
        if target.exists():
            try:
                dev = str(target.resolve())
                if shutil.which("findmnt"):
                    out = subprocess.check_output(["findmnt", "-n", "-o", "TARGET", dev], text=True).strip()
                    if out:
                        return Path(out)
            except Exception:
                pass

    # 4) fallback: scan /media & /run/media for the label directory names
    for root in (Path("/media"), Path("/run/media"), Path("/mnt"), Path("/Volumes")):
        if root.exists():
            for candidate in root.rglob(label):
                if candidate.is_dir():
                    return candidate

    # 5) optional psutil fallback (best-effort, psutil not required)
    try:
        import psutil  # type: ignore
    except Exception:
        psutil = None
    if psutil:
        try:
            for p in psutil.disk_partitions(all=False):
                mnt = Path(p.mountpoint)
                if mnt.name == label or (mnt.exists() and (mnt / label).exists()):
                    return mnt
        except Exception:
            pass

    # not found
    return None

# ---------- flash operations ----------
def find_default_uf2(manifest_path: Path) -> Optional[Path]:
    # prefer explicit build/platforms/*/firmware.uf2 or build/*.uf2
    candidates = [
        manifest_path.parent / "build" / "*.uf2",
        manifest_path.parent / "build" / "platforms" / "*" / "*.uf2",
    ]
    for pattern in candidates:
        for p in Path().glob(str(pattern)):
            return p.resolve()
    return None

def flash_uf2(uf2_path: Path, mount_label: str = "RP2350", wait_seconds: int = 0) -> bool:
    """Return True on success, False on failure."""
    if not uf2_path or not uf2_path.exists():
        echo_err(f"UF2 file not found: {uf2_path}")
        return False
    click.echo(f"UF2: {uf2_path}")

    mp = find_rpi_rp2_mount(mount_label)
    if mp:
        click.echo(f"Found Pico mass-storage at: {mp}")
        try:
            target = mp / uf2_path.name
            click.echo(f"Copying {uf2_path} -> {target}")
            shutil.copy2(str(uf2_path), str(target))
            # ensure data is flushed to the device on POSIX systems (best-effort)
            try:
                if hasattr(os, "sync"):
                    os.sync()
            except Exception:
                pass
            click.echo("Copy complete. Device should reboot to the new firmware.")
            return True
        except PermissionError:
            echo_err(f"Permission denied copying to {mp}. Try mounting with proper permissions or run with sudo.")
            return False
        except Exception as e:
            echo_err(f"Failed to copy UF2: {e}")
            return False

    # not found - optionally wait
    if wait_seconds and wait_seconds > 0:
        click.echo(f"Device not found — waiting up to {wait_seconds}s for BOOTSEL mount (press BOOTSEL + plug)...")
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            mp = find_rpi_rp2_mount(mount_label)
            if mp:
                click.echo(f"Detected mount at {mp} — copying now...")
                try:
                    shutil.copy2(str(uf2_path), str(mp / uf2_path.name))
                    try:
                        if hasattr(os, "sync"):
                            os.sync()
                    except Exception:
                        pass
                    click.echo("Copy complete. Device should reboot to the new firmware.")
                    return True
                except Exception as e:
                    echo_err(f"Failed to copy UF2 after mount detection: {e}")
                    return False
            time.sleep(0.5)

    click.echo("Pico mass-storage device not detected automatically.")
    click.echo("Instructions:")
    click.echo("  1) Press and hold BOOTSEL on the Pico, plug the board into USB, release BOOTSEL.")
    click.echo("  2) It should appear as a removable volume named 'RP2350' (or similar).")
    click.echo(f"  3) Copy the UF2 file manually: cp {uf2_path} /path/to/RP2350/")
    echo_err("UF2 flashing aborted: device not mounted.")
    return False

def expand_placeholders(cmd: str, manifest_path: Path, elf: Optional[Path], uf2: Optional[Path]) -> str:
    cmd = cmd.replace("{build_dir}", str((manifest_path.parent / "build").resolve()))
    if elf:
        cmd = cmd.replace("{elf}", str(elf.resolve()))
    if uf2:
        cmd = cmd.replace("{uf2}", str(uf2.resolve()))
    return cmd

def flash_picotool(manifest_path: Path, picotool_cmd: Optional[str], elf_path: Optional[Path], uf2_path: Optional[Path]) -> bool:
    """Return True on success, False on failure."""
    # If manifest gives a command string, expand placeholders; otherwise fallback to "picotool load <elf>"
    if picotool_cmd:
        full = expand_placeholders(picotool_cmd, manifest_path, elf_path, uf2_path)
        return run_cmd(full, cwd=manifest_path.parent)

    # fallback: look for picotool in pico-sdk built deps or PATH
    candidates = [
        shutil.which("picotool"),
        (manifest_path.parent / "build" / "_deps" / "picotool" / "picotool"),
        (manifest_path.parent / "third_party" / "pico-sdk" / "build" / "_deps" / "picotool" / "picotool"),
    ]
    pic = next((str(p) for p in candidates if p and Path(p).exists()), None)
    if not pic:
        echo_err("picotool not found. Either install it on the host or provide 'picotool_cmd' in platform.yaml.")
        return False

    if elf_path and elf_path.exists():
        return run_cmd([pic, "load", str(elf_path.resolve())], cwd=manifest_path.parent)
    elif uf2_path and uf2_path.exists():
        return run_cmd([pic, "load", str(uf2_path.resolve())], cwd=manifest_path.parent)
    else:
        echo_err("picotool method selected but no ELF/UF2 found. Provide elf/uf2 or set picotool_cmd in manifest.")
        return False

def flash_openocd(manifest_path: Path, openocd_cmd: Optional[str], elf_path: Optional[Path], uf2_path: Optional[Path]) -> bool:
    """Return True on success, False on failure."""
    if not openocd_cmd:
        echo_err("openocd method requested but no 'openocd_cmd' provided in manifest.")
        return False
    full = expand_placeholders(openocd_cmd, manifest_path, elf_path, uf2_path)
    return run_cmd(full, cwd=manifest_path.parent)

# ---------- CLI ----------
@click.command()
@click.option("--platform", "-p", "platform", required=True, help="Platform folder under platforms/ (contains platform.yaml)")
@click.option("--method", "-m", "method", default=None, help="Force flash method (uf2_copy|picotool|openocd).")
@click.option("--uf2", "uf2_override", default=None, help="Path to UF2 file to flash (absolute preferred).")
@click.option("--elf", "elf_override", default=None, help="Path to ELF file to flash (absolute preferred).")
@click.option("--wait", "wait_seconds", default=0, type=int, help="For uf2_copy: wait up to N seconds for device to appear before failing.")
def main(platform: str, method: Optional[str], uf2_override: Optional[str], elf_override: Optional[str], wait_seconds: int) -> bool:
    manifest, manifest_path = load_manifest(platform)
    if manifest is None or manifest_path is None:
        # load_manifest already printed an error
        return False

    flash = manifest.get("flash", {}) or {}
    method = (method or flash.get("method") or "uf2_copy").lower()

    # resolve files (prefer overrides)
    uf2_rel = flash.get("uf2_file")
    elf_rel = flash.get("elf_file") or flash.get("elf") or flash.get("build_elf") or "build/firmware.elf"

    uf2_path = Path(uf2_override).resolve() if uf2_override else abspath_from_manifest(manifest_path, uf2_rel)
    elf_path = Path(elf_override).resolve() if elf_override else abspath_from_manifest(manifest_path, elf_rel)

    # fallback to find one in build
    if method == "uf2_copy" and (not uf2_path or not uf2_path.exists()):
        alt = find_default_uf2(manifest_path)
        if alt:
            uf2_path = alt
            click.echo(f"Auto-detected UF2: {uf2_path}")

    click.echo(f"Platform: {platform}")
    click.echo(f"Method: {method}")

    ok = True
    if method == "uf2_copy":
        if not uf2_path or not uf2_path.exists():
            click.echo(f"UF2 not found at {uf2_path}" if uf2_path else "No UF2 file provided.")
            # still attempt waiting if user wanted that
        ok = flash_uf2(uf2_path, mount_label=flash.get("uf2_mount_label", "RP2350"), wait_seconds=wait_seconds)

    elif method == "picotool":
        picotool_cmd = flash.get("picotool_cmd")
        ok = flash_picotool(manifest_path, picotool_cmd, elf_path, uf2_path)

    elif method == "openocd":
        openocd_cmd = flash.get("openocd_cmd")
        ok = flash_openocd(manifest_path, openocd_cmd, elf_path, uf2_path)

    else:
        echo_err(f"Unsupported flash method: {method}")
        return False

    if ok:
        click.echo("Flash step finished. If device didn't reboot, check connections.")
        click.echo("Docker notes: for picotool/openocd you need USB device access (e.g. --device /dev/bus/usb or --privileged).")
        click.echo("If permissions problems occur, add appropriate udev rules on the host for the device's VID/PID.")
        return True
    else:
        echo_err("Flash step failed. See errors above.")
        return False


if __name__ == "__main__":
    # main() returns a bool — map it to an exit code for CLI behaviour
    main()  # click will actually handle invocation; this call is for explicit script usage
