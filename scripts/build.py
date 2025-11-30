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
scripts/build.py

Build driver for multi-platform micro-ROS firmware (CMake + PlatformIO backends).
Loads repo-wide constants from scripts/const.yaml.

CLI: minimal surface: --platform/-p and repeatable --extra-arg/-e.
Requires: click, pyyaml
    python3 -m pip install --user click pyyaml
"""

from __future__ import annotations
import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import click

# -----------------------
# Load constants from YAML
# -----------------------
HERE = Path(__file__).resolve().parent
CONST_PATH = HERE / "const.yaml"

FALLBACK_CONSTS = {
    "supported_backends": ["cmake", "platformio"],
    "artifact_extensions": ["*.elf", "*.uf2", "*.bin", "*.hex", "*.a", "*.so", "*.o"],
    "defaults": {"config": "Release", "jobs": 4},
    "clean_env_var": "BUILD_CLEAN",
    "cmake_binary": "cmake",
    "platformio_binary": "pio",  # can be overridden in const.yaml
}


def load_constants() -> Dict[str, Any]:
    if CONST_PATH.exists() is False:
        click.echo(f"[warning] const.yaml not found at {CONST_PATH}; using builtin defaults", err=True)
        return FALLBACK_CONSTS.copy()

    try:
        data = yaml.safe_load(CONST_PATH.read_text()) or {}
        for k, v in FALLBACK_CONSTS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception as e:
        click.echo(f"[warning] Failed to parse const.yaml ({CONST_PATH}): {e} — using defaults", err=True)
        return FALLBACK_CONSTS.copy()


CONST = load_constants()


# -----------------------
# Exceptions & utilities
# -----------------------
class BuildError(Exception):
    pass

def fatal(msg: str, rc: int = 1) -> None:
    click.echo(f"[error] {msg}", err=True)
    sys.exit(rc)

def abspath_from_manifest(manifest_path: Path, value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return (manifest_path.parent / p).resolve()

def stream_subprocess(cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> bool:
    click.echo("+ " + " ".join(cmd))
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    assert proc.stdout is not None
    try:
        for line in proc.stdout:
            click.echo(line.rstrip())
    finally:
        proc.wait()

    if proc.returncode != 0:
        print(f"ERROR: {proc.returncode}: {cmd}")  # TODO fatal error -> terminate process
        return False

    return True

def list_artifacts(build_dir: Path) -> List[Path]:
    if not build_dir.exists():
        return []
    exts = CONST.get("artifact_extensions", [])
    out: List[Path] = []
    for pattern in exts:
        out.extend(list(build_dir.rglob(pattern)))
    out.extend([p for p in build_dir.iterdir() if p.is_file() and p.suffix == ""])
    uniq = sorted(set(out))
    return uniq


# -----------------------
# Backend interface
# -----------------------
class BuildBackend:
    def __init__(self, manifest: Dict[str, Any], manifest_path: Path, build_dir: Path, extra_args: List[str]):
        self.manifest = manifest
        self.manifest_path = manifest_path
        self.build_dir = build_dir
        self.extra_args = list(extra_args or [])
        self.env = self._prepare_env()
        defaults = CONST.get("defaults", {})
        self.config = str(manifest.get("build", {}).get("config", defaults.get("config", "Release")))
        self.jobs = int(manifest.get("build", {}).get("jobs", defaults.get("jobs", os.cpu_count() or 2)))

    def _prepare_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        if isinstance(self.manifest.get("env"), dict):
            for k, v in self.manifest["env"].items():
                env[str(k)] = str(v)
        return env

    def validate(self) -> None:
        raise NotImplementedError

    def clean(self) -> bool:
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            click.echo(f"Clean: removed {self.build_dir}")

    def configure(self) -> bool:
        raise NotImplementedError

    def build(self) -> bool:
        raise NotImplementedError

# -----------------------
# CMake backend
# -----------------------
class CMakeBackend(BuildBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        entry = self.manifest.get("build", {}).get("entry")
        if not entry:
            raise BuildError("manifest.build.entry is required for cmake backend")
        self.entry = abspath_from_manifest(self.manifest_path, entry)
        toolchain = self.manifest.get("toolchain_file")
        self.toolchain_file = abspath_from_manifest(self.manifest_path, toolchain) if toolchain else None
        cmake_args = self.manifest.get("build", {}).get("cmake_args", [])
        if isinstance(cmake_args, str):
            self.cmake_args = [cmake_args]
        elif isinstance(cmake_args, list):
            self.cmake_args = cmake_args
        else:
            self.cmake_args = []

    def validate(self) -> None:
        if not self.entry.exists():
            raise BuildError(f"CMake entry path does not exist: {self.entry}")
        if self.toolchain_file and not self.toolchain_file.exists():
            raise BuildError(f"toolchain_file declared but not found: {self.toolchain_file}")

    def configure(self) -> bool:
        cmake_bin = CONST.get("cmake_binary", "cmake")
        if shutil.which(cmake_bin) is None:
            raise BuildError(f"{cmake_bin} not found in PATH")
        self.build_dir.mkdir(parents=True, exist_ok=True)
        cmd = [cmake_bin, "-S", str(self.entry), "-B", str(self.build_dir), f"-DCMAKE_BUILD_TYPE={self.config}"]
        if self.toolchain_file:
            cmd.append(f"-DCMAKE_TOOLCHAIN_FILE={str(self.toolchain_file)}")
            cmd.append(f"-DCMAKE_TOOLCHAIN_FILE={str(self.toolchain_file.resolve())}")
        if self.env.get("PICO_SDK_PATH"):
            cmd.append(f"-DPICO_SDK_PATH={self.env['PICO_SDK_PATH']}")
        cmd.extend(self.cmake_args)
        cmd.extend(self.extra_args)
        status = stream_subprocess(cmd, cwd=self.build_dir, env=self.env)
        if status is False:
            return False
        return True

    def build(self) -> bool:
        cmd = [
            "cmake",
            "--build", str(self.build_dir),
            "--", f"-j{self.jobs}"
        ]
        status = stream_subprocess(cmd, cwd=self.build_dir, env=self.env)
        if status is False:
            return False
        return True

# -----------------------
# PlatformIO backend
# -----------------------
class PlatformIOBackend(BuildBackend):
    """
    PlatformIO backend:
    - manifest.build.entry -> path to folder containing platformio.ini
    - manifest.build.env -> optional environment name (PIO 'env') to build (string)
    - manifest.build.platformio_args -> optional list of extra args to pass to pio run
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        entry = self.manifest.get("build", {}).get("entry")
        if not entry:
            raise BuildError("manifest.build.entry is required for platformio backend")
        self.entry = abspath_from_manifest(self.manifest_path, entry)
        self.pio_env = self.manifest.get("build", {}).get("env")  # optional
        pio_args = self.manifest.get("build", {}).get("platformio_args", [])
        if isinstance(pio_args, str):
            self.pio_args = [pio_args]
        elif isinstance(pio_args, list):
            self.pio_args = pio_args
        else:
            self.pio_args = []

        # platformio binary to use (const override)
        self.pio_bin = CONST.get("platformio_binary", "pio")

    def validate(self) -> None:
        if not self.entry.exists():
            raise BuildError(f"PlatformIO entry path does not exist: {self.entry}")
        if not (self.entry / "platformio.ini").exists():
            raise BuildError(f"platformio.ini not found in entry directory: {self.entry}")
        if shutil.which(self.pio_bin) is None and shutil.which("platformio") is None:
            raise BuildError(f"PlatformIO CLI not found (tried '{self.pio_bin}' and 'platformio'). Install via 'pip install -U platformio'")

    def configure(self) -> None:
        # PlatformIO projects don't need a separate configure step in many cases.
        # We will still run 'pio init' only when the project is empty or if the manifest requests it.
        # If user provided extra arguments, nothing else to do here.
        click.echo("PlatformIO backend: no configure step (entry is platformio.ini based)")

    def build(self) -> bool:
        # prefer explicit binary if present
        pio_exe = shutil.which(self.pio_bin) or shutil.which("platformio") or self.pio_bin
        cmd = [pio_exe, "run", "-d", str(self.entry)]
        # if environment specified, add it
        if self.pio_env:
            cmd.extend(["-e", str(self.pio_env)])
        # add extra args from manifest + CLI
        cmd.extend(self.pio_args)
        # append CLI extra-args as-is
        cmd.extend(self.extra_args)
        # run
        status = stream_subprocess(cmd, cwd=self.entry, env=self.env)
        if status is False:
            return False
        return True

    def clean(self) -> bool:
        pio_exe = shutil.which(self.pio_bin) or shutil.which("platformio") or self.pio_bin
        cmd = [pio_exe, "run", "-d", str(self.entry), "-t", "clean"]
        status = stream_subprocess(cmd, cwd=self.entry, env=self.env)
        if status is False:
            return False
        return True

    def __str__(self):
        return f"<PlatformIOBackend entry={self.entry} env={self.pio_env}>"

# -----------------------
# Backend registry
# -----------------------
BACKENDS: Dict[str, Any] = {
    "cmake": CMakeBackend,
    "platformio": PlatformIOBackend,
}

# -----------------------
# Manifest loader & validator
# -----------------------
def load_manifest(platform_name: str) -> tuple[Dict[str, Any], Path]:
    manifest_path = Path("platforms") / platform_name / "platform.yaml"
    if not manifest_path.exists():
        raise BuildError(f"Platform manifest not found at: {manifest_path}")
    with open(manifest_path, "r") as fh:
        manifest = yaml.safe_load(fh) or {}
    if not isinstance(manifest, dict):
        raise BuildError("platform.yaml must be a YAML mapping at the top level")
    if "name" in manifest and manifest["name"] != platform_name:
        raise BuildError(f"platform.yaml 'name' != platform folder name (got '{manifest['name']}' vs '{platform_name}')")
    return manifest, manifest_path

def ensure_required_manifest_keys(manifest: Dict[str, Any]) -> None:
    if "build" not in manifest or not isinstance(manifest["build"], dict):
        raise BuildError("manifest must contain top-level 'build' mapping")
    if "type" not in manifest["build"]:
        raise BuildError("manifest.build.type is required (e.g. 'cmake' or 'platformio')")

# -----------------------
# CLI
# -----------------------
@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option("--platform", "-p", "platform", required=True, help="Platform folder under platforms/ (contains platform.yaml)")
@click.option("--extra-arg", "-e", "extra_args", multiple=True, help="Extra arg passed to backend configure/build (repeatable).")
def main(platform: str, extra_args: List[str]):
    try:
        manifest, manifest_path = load_manifest(platform)
        ensure_required_manifest_keys(manifest)
    except BuildError as exc:
        fatal(str(exc), rc=2)

    build_type = manifest.get("build", {}).get("type", "cmake")
    supported = CONST.get("supported_backends", [])
    if build_type not in supported:
        click.echo(f"[warning] build.type '{build_type}' not listed in const.yaml supported_backends: {supported}")

    backend_cls = BACKENDS.get(build_type)
    if backend_cls is None:
        fatal(f"Unsupported build.type '{build_type}' in manifest. Implement backend in scripts/build.py and add to BACKENDS.", rc=3)

    build_dir = (manifest_path.parent / "build").resolve()
    backend = backend_cls(manifest, manifest_path, build_dir, list(extra_args))

    try:
        backend.validate()
    except BuildError as exc:
        fatal(str(exc), rc=4)

    clean_env_var = CONST.get("clean_env_var", "BUILD_CLEAN")
    if os.getenv(clean_env_var, "0") in ("1", "true", "True"):
        click.echo(f"{clean_env_var} detected: cleaning build dir first")
        status = backend.clean()
        if status is False:
            return

    click.echo(f"Building platform '{platform}' (backend={build_type})")
    click.echo(f"  build_dir: {build_dir}")
    click.echo(f"  jobs: {backend.jobs}  config: {backend.config}")

    try:
        status = backend.configure()
        if status is False:
            return

        status = backend.build()
        if status is False:
            return
    except subprocess.CalledProcessError as exc:
        fatal(f"Command failed (rc={exc.returncode}): {exc.cmd}", rc=5)
    except BuildError as exc:
        fatal(str(exc), rc=6)

    artifacts = list_artifacts(build_dir)
    if artifacts:
        click.echo("Build artifacts:")
        for p in artifacts:
            click.echo(f"  - {p}")
    else:
        # For PlatformIO projects the main artifacts are typically under .pio/build/<env>
        # If build_dir is empty try to look for .pio in the entry dir for platformio
        if build_type == "platformio":
            pio_entry = backend.entry if isinstance(backend, PlatformIOBackend) else None
            if pio_entry:
                pio_artifacts = list(pio_entry.rglob(".pio/build/*"))
                if pio_artifacts:
                    click.echo("PlatformIO artifacts (sample):")
                    for x in sorted(set(pio_artifacts))[:20]:
                        click.echo(f"  - {x}")
                    click.echo("Note: PlatformIO stores build output under .pio/build/<env> inside the project entry directory.")
                else:
                    click.echo("No artifacts found. Inspect the PlatformIO .pio/build directory.")
            else:
                click.echo("No common artifacts found under build dir. Inspect the build directory manually.")
        else:
            click.echo("No common artifacts found under build dir. Inspect the build directory manually.")

    click.echo("Build completed successfully.")


if __name__ == "__main__":
    main()
