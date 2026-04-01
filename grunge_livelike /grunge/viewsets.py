from rest_framework import viewsets

from .filters import AlbumFilter, ArtistFilter, PlaylistFilter, TrackFilter
from .models import Album, Artist, Playlist, Track
from .serializers import (
    AlbumSerializer,
    ArtistSerializer,
    PlaylistSerializer,
    TrackSerializer,
)


class BaseAPIViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"


class ArtistViewSet(BaseAPIViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    filterset_class = ArtistFilter


class AlbumViewSet(BaseAPIViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    filterset_class = AlbumFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related("artist").prefetch_related("tracks")


class TrackViewSet(BaseAPIViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    filterset_class = TrackFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related("album", "album__artist")


class PlaylistViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    serializer_class = PlaylistSerializer
    filterset_class = PlaylistFilter

    def get_queryset(self):
        return Playlist.objects.prefetch_related(
            "playlist_tracks__track__album__artist"
        ).order_by("name")
