"""Source-level contracts of the particle scene (behaviour is checked in the browser)."""
import re

from htmltree import read

JS = read("assets/axolotl.v1.js")


def test_finger_pushes_particles_on_touch_screens():
    assert re.search(r"addEventListener\('touch(start|move)'", JS)


def test_scroll_speed_drives_swimming():
    assert "uSwim" in JS and "uPhase" in JS
    assert "scrollY - lastScroll" in JS


def test_android_tilt_without_ios_permission_prompt():
    assert "deviceorientation" in JS
    assert "requestPermission" in JS          # detected, so iOS is skipped rather than prompted


def test_more_idle_motion_on_small_screens():
    assert re.search(r"uLife: \{ value: small \? 1\.\d+ : 1 \}", JS)
