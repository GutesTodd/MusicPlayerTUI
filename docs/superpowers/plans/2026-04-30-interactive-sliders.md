# Interactive Sliders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement interactive, draggable sliders for track progress and volume in the UI.

**Architecture:** 
- Custom `InteractiveSlider` widget using Textual's mouse event handling.
- Event-driven communication between the slider and the `PlayerViewModel`.
- Throttled/Debounced updates to prevent socket flooding during dragging.

**Tech Stack:** Python 3.12+, Textual.

---

### Task 1: Create InteractiveSlider Widget

**Files:**
- Create: `ui/widgets/slider.py`

- [ ] **Step 1: Implement the InteractiveSlider class**
Implement a custom widget that handles mouse drag events and renders a beautiful bar with a thumb.

```python
from __future__ import annotations
from typing import ClassVar
from textual.widget import Widget
from textual.events import MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.reactive import reactive
from rich.text import Text

class InteractiveSlider(Widget, can_focus=True):
    DEFAULT_CSS = """
    InteractiveSlider {
        width: 100%;
        height: 1;
        min-height: 1;
        margin: 0 1;
    }
    InteractiveSlider.-dragging {
        color: $accent;
    }
    """

    class Changed(Message):
        def __init__(self, value: float) -> None:
            super().__init__()
            self.value = value

    class Seeked(Message):
        def __init__(self, value: float) -> None:
            super().__init__()
            self.value = value

    value: reactive[float] = reactive(0.0)
    _dragging: bool = False

    def render(self) -> Text:
        width = self.size.width
        if width <= 0:
            return Text("")
            
        filled_width = int(self.value * width)
        
        text = Text()
        # Filled part
        text.append("━" * max(0, filled_width - 1), style="$accent")
        # Thumb
        text.append("●", style="white" if not self._dragging else "$accent")
        # Unfilled part
        text.append("━" * max(0, width - filled_width), style="$text-muted")
        
        return text

    def _update_value_from_mouse(self, x: int) -> None:
        width = self.size.width
        if width > 0:
            self.value = max(0.0, min(1.0, x / width))
            self.post_message(self.Changed(self.value))

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.add_class("-dragging")
        self.capture_mouse()
        self._update_value_from_mouse(event.x)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            self._update_value_from_mouse(event.x)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.remove_class("-dragging")
            self.release_mouse()
            self.post_message(self.Seeked(self.value))
```

- [ ] **Step 2: Commit**
```bash
git add ui/widgets/slider.py
git commit -m "feat: add InteractiveSlider widget"
```

### Task 2: Update PlayerViewModel for Seeking

**Files:**
- Modify: `ui/viewmodels/player.py`

- [ ] **Step 1: Add seek method to PlayerViewModel**
```python
    async def seek(self, position_ms: int) -> None:
        logger.info(f"Запрос на перемотку: {position_ms}ms")
        response = await self._client.send_command(
            "playback.seek", {"position_ms": position_ms}
        )
        if response and response.get("status") == "ok":
            self.position_ms = position_ms
            self.notify()
```

- [ ] **Step 2: Commit**
```bash
git add ui/viewmodels/player.py
git commit -m "feat: add seek support to PlayerViewModel"
```

### Task 3: Integrate Sliders into PlayerBar

**Files:**
- Modify: `ui/widgets/player_bar.py`

- [x] **Step 1: Replace ProgressBar with InteractiveSlider**
Import `InteractiveSlider` and swap widgets in `compose`.

```python
from ui.widgets.slider import InteractiveSlider

# In PlayerBar.compose:
# Replace ProgressBar(id="track_progress") with InteractiveSlider(id="track_progress")
# Replace ProgressBar(id="volume_bar") with InteractiveSlider(id="volume_bar")
```

- [x] **Step 2: Add event handlers for Sliders**
```python
    @on(InteractiveSlider.Changed, "#volume_bar")
    def on_volume_change(self, event: InteractiveSlider.Changed) -> None:
        # Update volume in real-time
        self.app.player_vm.volume = int(event.value * 100)
        self.run_worker(self.app.player_vm.set_volume(self.app.player_vm.volume))

    @on(InteractiveSlider.Changed, "#track_progress")
    def on_track_progress_dragging(self, event: InteractiveSlider.Changed) -> None:
        # Just update UI time code while dragging
        self.app.player_vm.position_ms = int(event.value * self.app.player_vm.duration_ms)
        self.app._on_player_update()

    @on(InteractiveSlider.Seeked, "#track_progress")
    def on_track_seek(self, event: InteractiveSlider.Seeked) -> None:
        target_ms = int(event.value * self.app.player_vm.duration_ms)
        self.run_worker(self.app.player_vm.seek(target_ms))
```

- [x] **Step 3: Commit**
```bash
git add ui/widgets/player_bar.py
git commit -m "refactor: use InteractiveSlider in PlayerBar"
```

### Task 4: Implement Hotkeys and Final Polish

**Files:**
- Modify: `ui/main.py`
- Modify: `ui/views/statics/app.tcss`

- [x] **Step 1: Update BINDINGS and Action handlers**
Add bindings for Arrows, `[`, `]`, `-`, `+`.

```python
    BINDINGS = [
        # ... existing ...
        Binding("right", "seek_forward(5000)", "Вперед 5с", show=False),
        Binding("left", "seek_backward(5000)", "Назад 5с", show=False),
        Binding("]", "seek_forward(30000)", "Вперед 30с", show=False),
        Binding("[", "seek_backward(30000)", "Назад 30с", show=False),
        Binding("up", "volume_up(5)", "Громкость +5%", show=False),
        Binding("down", "volume_down(5)", "Громкость -5%", show=False),
        Binding("+", "volume_up(10)", "Громкость +10%", show=False),
        Binding("=", "volume_up(10)", "Громкость +10%", show=False), # Handle both + and =
        Binding("-", "volume_down(10)", "Громкость -10%", show=False),
    ]

    def action_seek_forward(self, ms: int) -> None:
        target = min(self.player_vm.duration_ms, self.player_vm.position_ms + ms)
        self.run_worker(self.player_vm.seek(target))

    def action_seek_backward(self, ms: int) -> None:
        target = max(0, self.player_vm.position_ms - ms)
        self.run_worker(self.player_vm.seek(target))

    def action_volume_up(self, percent: int) -> None:
        self.run_worker(self.player_vm.set_volume(self.player_vm.volume + percent))

    def action_volume_down(self, percent: int) -> None:
        self.run_worker(self.player_vm.set_volume(self.player_vm.volume - percent))
```

- [x] **Step 2: Update Slider value in _on_player_update**
Ensure the slider updates its position when the track plays normally.

```python
    # In ui/main.py _on_player_update:
    track_progress = self.query_one("#track_progress", InteractiveSlider)
    if self.player_vm.duration_ms > 0 and not track_progress._dragging:
        track_progress.value = self.player_vm.position_ms / self.player_vm.duration_ms
        
    volume_bar = self.query_one("#volume_bar", InteractiveSlider)
    if not volume_bar._dragging:
        volume_bar.value = self.player_vm.volume / 100
```

- [x] **Step 3: Commit and Final Verify**
Run the app and test all interactions.
```bash
git commit -a -m "feat: complete interactive sliders with hotkeys"
```
