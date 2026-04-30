from __future__ import annotations

import math
import random
from typing import Final

from textual.widgets import Static


class Visualizer(Static):
    def on_mount(self) -> None:
        self.width_cells: int = 30
        self.points: list[float] = [0.0] * self.width_cells
        self.phase: float = 0.0
        self.set_interval(0.05, self._update_wave)

    def _update_wave(self) -> None:
        from ui.main import MusicPlayerApp

        app = self.app
        if not isinstance(app, MusicPlayerApp):
            return

        if app.player_vm.is_playing:
            self.phase += 0.5
            self.points = [
                (math.sin(self.phase + i * 0.5) * 2 + random.uniform(-1, 1))
                for i in range(self.width_cells)
            ]
            self.update(self._render_wave())
        else:
            self.points = [p * 0.8 for p in self.points]
            self.update(self._render_wave())

    def _render_wave(self) -> str:
        glyphs: Final = " ▂▃▄▅▆▇█"
        res = ""
        for p in self.points:
            idx = int(abs(p) * 2) % len(glyphs)
            color = "$accent" if abs(p) < 1.5 else "white"
            res += f"[{color}]{glyphs[idx]}[/]"
        return res
