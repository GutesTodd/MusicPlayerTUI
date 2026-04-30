from typing import Literal
from uuid import uuid4

from shared.domain import entities


class InMemoryQueueManager:
    def __init__(self) -> None:
        self._queue = entities.TrackQueue(id=uuid4())
        self.repeat_mode = "none"

    async def set_queue(self, queue: entities.TrackQueue) -> None:
        self._queue = queue

    async def get_current(self) -> entities.Track | None:
        return self._queue.current.track if self._queue.current else None

    async def get_all(self) -> list[entities.Track] | None:
        tracks = []
        node = self._queue.head
        while node:
            tracks.append(node.track)
            node = node.next
        return tracks

    async def add_track(
        self, track: entities.Track, position: Literal["next", "end"] = "end"
    ) -> None:
        new_node = entities.QueueNode(id=uuid4(), track=track)

        if not self._queue.head or not self._queue.tail:
            self._queue.head = new_node
            self._queue.tail = new_node
            self._queue.current = new_node
            self._queue.length = 1
            return

        tail = self._queue.tail
        current = self._queue.current

        if position == "end":
            new_node.prev = self._queue.tail
            tail.next = new_node
            self._queue.tail = new_node

        elif position == "next":
            if not current:
                new_node.prev = self._queue.tail
                tail.next = new_node
                self._queue.tail = new_node
            else:
                old_next = current.next
                new_node.prev = current
                new_node.next = old_next
                current.next = new_node

                if old_next:
                    old_next.prev = new_node
                else:
                    self._queue.tail = new_node

    async def next_track(self) -> entities.Track | None:
        if not self._queue.current or not self._queue.current.next:
            return None
        if self.repeat_mode == "one":
            return self._queue.current.track
        if not self._queue.current.next and self.repeat_mode == "all":
            self._queue.current = self._queue.head
            return self._queue.current.track if self._queue.current else None
        self._queue.current = self._queue.current.next
        return self._queue.current.track

    async def prev_track(self) -> entities.Track | None:
        if not self._queue.current or not self._queue.current.prev:
            return None
        self._queue.current = self._queue.current.prev
        return self._queue.current.track

    async def clear(self) -> None:
        self._queue = entities.TrackQueue(id=uuid4())

    async def remove_track(self, node_id: str) -> None:
        curr = self._queue.head
        while curr:
            if str(curr.id) == node_id:
                if self._queue.current == curr:
                    self._queue.current = curr.next or curr.prev
                if curr.prev:
                    curr.prev.next = curr.next
                else:
                    self._queue.head = curr.next
                if curr.next:
                    curr.next.prev = curr.prev
                else:
                    self._queue.tail = curr.prev

                self._queue.length -= 1
                break
            curr = curr.next

    async def set_repeat_mode(self, mode: str) -> None:
        self.repeat_mode = mode
