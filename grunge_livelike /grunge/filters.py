from django_filters import rest_framework as filters

from .models import Album, Artist, Playlist, Track


class ArtistFilter(filters.FilterSet):

    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Artist
        fields = ("name",)


class AlbumFilter(filters.FilterSet):

    artist_uuid = filters.UUIDFilter("artist__uuid")
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Album
        fields = ("artist_uuid", "name")


class TrackFilter(filters.FilterSet):

    album_uuid = filters.UUIDFilter("album__uuid")
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Track
        fields = ("album_uuid", "name")


class PlaylistFilter(filters.FilterSet):

    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Playlist
        fields = ("name",)
