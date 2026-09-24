"""SYNTHETIC test fixture. Not the HW1 target application."""
import subprocess

from app.settings import HOOK


def run_hook(user):
    command = HOOK % {"user": user}
    return subprocess.run(command, shell=True, check=False)
