# Codebase Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix critical linting errors and improve architectural integrity as identified by Ruff.

**Architecture:** 
- Solve circular dependencies in domain entities using PEP 563.
- Ensure asyncio tasks are not garbage collected by storing references.
- Modernize file operations using `pathlib`.
- Standardize enums with `StrEnum`.

**Tech Stack:** Python 3.12+, asyncio, pathlib, Pydantic.

---

### Task 1: Fix Circular Dependencies in Entities

**Files:**
- Modify: `shared/domain/entities.py`

- [ ] **Step 1: Add annotations import and fix types**
Add `from __future__ import annotations` at the top. This allows types to be used before they are fully defined.

```python
from __future__ import annotations
from enum import StrEnum
from pydantic import Field
from shared.domain.common import BaseEntity

class RepeatMode(StrEnum):
    NONE = "none"
    ONE = "one"
    ALL = "all"

# ... rest of the classes ...
```

- [ ] **Step 2: Commit**
```bash
git add shared/domain/entities.py
git commit -m "refactor: fix circular dependencies in entities"
```

### Task 2: Standardize Enums to StrEnum

**Files:**
- Modify: `backend/contexts/auth/domain.py`

- [ ] **Step 1: Change AuthStatusEnum to inherit from StrEnum**
```python
from enum import StrEnum

class AuthStatusEnum(StrEnum):
    IDLE = "idle"
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
```

- [ ] **Step 2: Commit**
```bash
git add backend/contexts/auth/domain.py
git commit -m "refactor: use StrEnum for AuthStatus"
```

### Task 3: Secure Asyncio Tasks (GC Protection)

**Files:**
- Modify: `backend/contexts/auth/use_cases/yandex_flow.py`
- Modify: `ui/viewmodels/auth.py`

- [ ] **Step 1: Add a set to store task references in YandexAuthFlow**
```python
class YandexAuthFlow:
    def __init__(self, ...):
        self._background_tasks = set()
        # ...
    
    async def start(self, ...):
        # ...
        task = asyncio.create_task(self._wait_for_completion(...))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
```

- [ ] **Step 2: Add a set to store task references in AuthViewModel**
```python
class AuthViewModel:
    def __init__(self, ...):
        self._tasks = set()
        # ...

    async def start_auth(self, ...):
        # ...
        task = asyncio.create_task(self._poll_auth_status(...))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
```

- [ ] **Step 3: Commit**
```bash
git add backend/contexts/auth/use_cases/yandex_flow.py ui/viewmodels/auth.py
git commit -m "refactor: protect background tasks from garbage collection"
```

### Task 4: Modernize File Operations with Pathlib

**Files:**
- Modify: `backend/infrastructure/config/service.py`
- Modify: `backend/main.py`
- Modify: `launcher.py`

- [ ] **Step 1: Replace os.path and open() in config service**
```python
from pathlib import Path

# Use self.config_path.read_text() and self.config_path.write_text()
```

- [ ] **Step 2: Replace os.path in backend/main.py**
```python
from pathlib import Path
# log_file = Path("log/yandex_music_backend/daemon.log").expanduser()
```

- [ ] **Step 3: Replace os.path in launcher.py**
```python
from pathlib import Path
# base_dir = Path(__file__).parent.resolve()
```

- [ ] **Step 4: Commit**
```bash
git add backend/infrastructure/config/service.py backend/main.py launcher.py
git commit -m "refactor: modernize file and path operations with pathlib"
```

### Task 5: Modularize UI (Move widgets out of main.py)

**Files:**
- Create: `ui/widgets/visualizer.py`
- Create: `ui/widgets/sidebar.py`
- Create: `ui/widgets/player_bar.py`
- Modify: `ui/main.py`

- [ ] **Step 1: Move Visualizer to ui/widgets/visualizer.py**
- [ ] **Step 2: Move Sidebar to ui/widgets/sidebar.py**
- [ ] **Step 3: Move TickerLabel and PlayerBar to ui/widgets/player_bar.py**
- [ ] **Step 4: Update imports in ui/main.py and cleanup**

- [ ] **Step 5: Commit**
```bash
git add ui/widgets/ ui/main.py
git commit -m "refactor: modularize UI by moving widgets to dedicated files"
```

### Task 6: Final Cleanup and Validation

- [ ] **Step 1: Run ruff check and fix**
Run: `uv run ruff check . --fix`

- [ ] **Step 2: Run ruff format**
Run: `uv run ruff format .`

- [ ] **Step 3: Commit final cleanup**
```bash
git commit -a -m "style: final ruff cleanup"
```
