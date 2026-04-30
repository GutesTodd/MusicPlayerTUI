from uuid import uuid4

from shared.domain import entities


class QueueFactory:
    @staticmethod
    async def create_queue(
        source: entities.Track
        | entities.Album
        | entities.Playlist
        | list[entities.Track],
    ) -> entities.TrackQueue:
        tracks = []
        if isinstance(source, entities.Track):
            tracks = [source]
        elif isinstance(source, (entities.Album, entities.Playlist)):
            tracks = source.tracks
        elif isinstance(source, list):
            tracks = source
        if not tracks:
            return entities.TrackQueue(id=uuid4())
        nodes = [entities.QueueNode(id=uuid4(), track=t) for t in tracks]
        for i in range(len(nodes)):
            if i > 0:
                nodes[i].prev = nodes[i - 1]
            if i < len(nodes) - 1:
                nodes[i].next = nodes[i + 1]

        return entities.TrackQueue(
            id=uuid4(),
            head=nodes[0],
            tail=nodes[-1],
            current=nodes[0],
            length=len(nodes),
        )
