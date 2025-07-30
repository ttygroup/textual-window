from typing import cast
from pathlib import Path
from textual.pilot import Pilot
from textual_window.demo import WindowDemo
# from .app_test import WindowTestApp

DEMO_DIR = Path(__file__).parent
TERINAL_SIZE = (110, 36)

async def test_launch():  
    """Test launching the WindowDemo app."""
    app = WindowDemo()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.exit(None) 

def test_snapshot_launch_only(snap_compare):

    async def run_before(pilot: Pilot[None]) -> None:
        await pilot.pause()

    assert snap_compare(
        DEMO_DIR / "app_test.py",
        terminal_size=TERINAL_SIZE,
        run_before=run_before,
    )