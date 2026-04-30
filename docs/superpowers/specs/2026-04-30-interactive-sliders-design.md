# Spec: Interactive Sliders for Progress and Volume

**Topic:** Replace static `ProgressBar` with interactive, draggable, and hotkey-supported sliders.

## 1. Goal
Provide a modern and "beautiful" way to control track position and volume using both mouse (drag-to-seek) and keyboard.

## 2. Architecture
- **Widget:** A new custom widget `InteractiveSlider` inheriting from `textual.widget.Widget`.
- **Communication:** 
    - UI updates `value` locally during dragging.
    - `SliderChanged` event is emitted on each change (throttled for volume).
    - `SliderSeeked` event is emitted on mouse release (for track seeking).
- **Data Flow:**
    - `PlayerViewModel` receives the new value and calls `client.send_command`.
    - `PlayerBar` updates its UI state based on the ViewModel.

## 3. UI Components
### `InteractiveSlider` Widget
- **Visuals:** 
    - Track: `━` character.
    - Thumb: `●` character.
    - Colors: `$accent` for the progress, `$text-muted` for the remaining part.
- **Interactions:**
    - `on_mouse_down`: Start dragging, jump to click position.
    - `on_mouse_move`: If dragging, update value relative to widget width.
    - `on_mouse_up`: End dragging, emit `Seeked` event.

### `PlayerBar` Update
- Replace `track_progress` (ProgressBar) with `InteractiveSlider`.
- Replace `volume_bar` (ProgressBar) with `InteractiveSlider`.

## 4. Hotkeys
Defined in `MusicPlayerApp.BINDINGS` and handled via ViewModel:
- **Seek Forward/Backward:** `Right`/`Left` arrows (+/- 5s), `[` / `]` (+/- 30s).
- **Volume Up/Down:** `Up`/`Down` arrows (+/- 5%), `-` / `+` (+/- 10%).

## 5. Viewmodel Changes (`PlayerViewModel`)
- `seek(position_ms)`: Sends `playback.seek` command.
- `set_volume(volume_level)`: Sends `playback.set_volume` (already exists, but will be used by the slider).

## 6. Testing Strategy
- **Manual Verification:** 
    - Drag progress bar: verify \"time code\" updates in real-time.
    - Release progress bar: verify music jumps to that position.
    - Scroll/Drag volume: verify volume changes.
    - Test all hotkeys.
- **Visual Check:** Ensure sliders align perfectly in the `PlayerBar`.
