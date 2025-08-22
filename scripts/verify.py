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
scripts/verify.py

Verify/connect smoke-test helper for micro-ROS clients.

Reads: platforms/<platform>/platform.yaml
Actions:
 - optionally launches a micro-ROS Agent (serial/usb_cdc/udp/tcp) based on manifest
 - polls `ros2 topic list` until the expected topic appears (default "/heartbeat")
 - returns exit code 0 on success, non-zero on failure

Usage:
  ./scripts/verify.py --platform rp2040
  ./scripts/verify.py -p rp2040 --topic /status --timeout 20
  ./scripts/verify.py -p rp2040 --no-agent   # when agent already running
  ./scripts/verify.py -p rp2040 --agent-cmd "ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0"
"""

from __future__ import annotations
import os
import sys
import time
import shlex
import signal
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import click

# -----------------------
# Helpers
# -----------------------
def fatal(msg: str, rc: int = 1) -> None:
    click.echo(f"[error] {msg}", err=True)
    sys.exit(rc)

def load_manifest(platform_name: str) -> (Dict[str, Any], Path):
    manifest_path = Path("platforms") / platform_name / "platform.yaml"
    if not manifest_path.exists():
        fatal(f"Platform manifest not found: {manifest_path}")
    with manifest_path.open("r") as fh:
        manifest = yaml.safe_load(fh) or {}
    return manifest, manifest_path

def build_default_agent_cmd(manifest: Dict[str, Any]) -> List[str]:
    """
    Build a sensible default micro-ROS Agent command from manifest.transport.
    Falls back to serial using dev_node if transport not recognized.
    """
    transport = manifest.get("transport", {}) or {}
    ttype = (transport.get("type") or "serial").lower()
    # base command using ros2 run micro_ros_agent micro_ros_agent ...
    base = ["ros2", "run", "micro_ros_agent", "micro_ros_agent"]
    if ttype in ("serial", "usb_cdc", "cdc-acm", "cdc"):
        dev = transport.get("dev_node") or transport.get("dev") or "/dev/ttyACM0"
        return base + ["serial", "--dev", dev]
    elif ttype in ("udp", "udp4", "udp6"):
        port = str(transport.get("port", 8888))
        return base + ["udp4", "--port", port]
    elif ttype in ("tcp", "tcp4", "tcp6"):
        port = str(transport.get("port", 8888))
        return base + ["tcp4", "--port", port]
    else:
        # unknown transport -> default to serial using dev_node if provided
        dev = transport.get("dev_node") or transport.get("dev")
        if dev:
            return base + ["serial", "--dev", dev]
        # nothing found, return base without args (user must override)
        return base

def run_agent_process(cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
    """
    Start agent subprocess and return Popen. Stdout/stderr forwarded to console.
    """
    # split if user passed a single string token list
    flat_cmd: List[str] = []
    for item in cmd:
        if isinstance(item, str) and any(ch in item for ch in " \t") and not item.startswith("-"):
            # when user passes the full command as single string via --agent-cmd, we should split it
            # but we assume top-level invocation uses list already. Use shlex when we detect a single string command.
            flat_cmd.extend(shlex.split(item))
        else:
            flat_cmd.append(item)
    click.echo(f"[agent] launching: {' '.join(flat_cmd)}")
    try:
        proc = subprocess.Popen(flat_cmd, cwd=str(cwd) if cwd else None, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    except FileNotFoundError:
        fatal(f"Agent executable not found (tried to run: {flat_cmd[0]}). Ensure 'ros2' and micro_ros_agent are installed and on PATH.")
    # Start a small thread-like pump to stream output to console without blocking; here we just read lines in background.
    # We'll not block here; but we want to show logs; we'll create a non-blocking printer loop in main.
    return proc

def stream_proc_output(proc: subprocess.Popen, prefix: str = "[agent] ") -> None:
    """
    Stream process stdout lines to console until none left (non-blocking use).
    Called after poll/termination to drain remaining output.
    """
    if proc.stdout is None:
        return
    for line in proc.stdout:
        click.echo(prefix + line.rstrip())

def ros2_topic_list() -> List[str]:
    """Return parsed list of ros2 topics from `ros2 topic list`."""
    try:
        out = subprocess.check_output(["ros2", "topic", "list"], text=True, stderr=subprocess.DEVNULL)
        topics = [t.strip() for t in out.splitlines() if t.strip()]
        return topics
    except subprocess.CalledProcessError:
        # ros2 command exists but returned non-zero
        return []
    except FileNotFoundError:
        fatal("`ros2` executable not found on PATH. Make sure you have a sourced ROS2 install in this shell.")

# -----------------------
# CLI
# -----------------------
@click.command()
@click.option("--platform", "-p", "platform", required=True, help="platform folder name (platforms/<name>/platform.yaml)")
@click.option("--topic", "-t", "topic", default="/heartbeat", help="Topic to wait for (default: /heartbeat)")
@click.option("--timeout", "-T", "timeout", default=20, type=int, help="Seconds to wait for topic to appear (default: 20)")
@click.option("--no-agent", is_flag=True, default=False, help="Do not start micro-ROS Agent (assume it is already running)")
@click.option("--agent-cmd", "agent_cmd", default=None, help="Override agent command (string). Example: \"ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0\"")
@click.option("--agent-args", "agent_args", multiple=True, help="Additional args appended to agent command (repeatable)")
@click.option("--poll-interval", "poll_interval", default=1.0, help="Seconds between ros2 topic list polls")
def main(platform: str, topic: str, timeout: int, no_agent: bool, agent_cmd: Optional[str], agent_args: List[str], poll_interval: float):
    # load manifest
    manifest, manifest_path = load_manifest(platform)
    transport = manifest.get("transport", {}) or {}
    click.echo(f"Platform: {platform}  transport: {transport.get('type', 'unknown')}")
    # build agent command
    if agent_cmd:
        # split the provided string into tokens
        cmd_list = shlex.split(agent_cmd)
    else:
        cmd_list = build_default_agent_cmd(manifest)
    # append agent_args (explicit)
    if agent_args:
        cmd_list = cmd_list + list(agent_args)

    agent_proc: Optional[subprocess.Popen] = None
    started_agent = False

    try:
        # start agent unless requested not to
        if not no_agent:
            agent_proc = run_agent_process(cmd_list, cwd=None, env=None)
            started_agent = True
            # give agent some time to start and enumerate transport
            click.echo("Waiting 2s for agent to initialize...")
            start_time = time.time()
            # while agent is running, we will poll ros2
            time.sleep(2)
        else:
            click.echo("Skipping agent start (--no-agent): assuming user started the agent externally.")

        # Poll for the topic
        click.echo(f"Polling `ros2 topic list` for topic '{topic}' (timeout {timeout}s)...")
        deadline = time.time() + timeout
        last_agent_output_ts = time.time()
        while time.time() < deadline:
            # if agent process ended prematurely, bail out
            if agent_proc and agent_proc.poll() is not None:
                # stream what's left of output then fail
                stream_proc_output(agent_proc)
                fatal(f"Agent process exited unexpectedly with code {agent_proc.returncode}. See logs above.", rc=10)
            try:
                topics = ros2_topic_list()
            except SystemExit:
                # ros2 not found -> fatal already called inside
                raise
            if topic in topics:
                click.echo(f"[ok] Topic '{topic}' found in ROS2 topic list.")
                # optionally stream some agent output to give context
                if agent_proc:
                    stream_proc_output(agent_proc)
                # success: exit 0
                # cleanup agent if we started it
                if agent_proc and started_agent:
                    click.echo("Stopping agent process...")
                    agent_proc.send_signal(signal.SIGINT)
                    try:
                        agent_proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        agent_proc.kill()
                sys.exit(0)
            # not found yet: print a short status line periodically
            click.echo(f"[waiting] topic not found yet. next check in {poll_interval}s...")
            time.sleep(poll_interval)
        # timeout reached
        click.echo(f"[fail] timed out waiting for topic '{topic}' (after {timeout}s).")
        # stream some agent output if we started it
        if agent_proc:
            stream_proc_output(agent_proc)
        # graceful cleanup
        if agent_proc and started_agent:
            click.echo("Stopping agent process...")
            agent_proc.send_signal(signal.SIGINT)
            try:
                agent_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                agent_proc.kill()
        # fail
        sys.exit(11)
    except KeyboardInterrupt:
        click.echo("Interrupted by user. Cleaning up...")
        if agent_proc and started_agent:
            agent_proc.send_signal(signal.SIGINT)
            try:
                agent_proc.wait(timeout=2)
            except Exception:
                agent_proc.kill()
        sys.exit(2)

if __name__ == "__main__":
    main()
