from django.db import transaction
from furl import furl
from rest_framework import serializers
from rest_framework.reverse import reverse as drf_reverse

from .fields import UUIDHyperlinkedIdentityField
from .models import Album, Artist, Playlist, PlaylistTrack, Track


class TrackAlbumArtistSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="artist-detail")

    class Meta:
        model = Artist
        fields = ("uuid", "url", "name")


class TrackAlbumSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="album-detail")
    artist = TrackAlbumArtistSerializer()

    class Meta:
        model = Album
        fields = ("uuid", "url", "name", "artist")


class TrackSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="track-detail")
    album = TrackAlbumSerializer()

    class Meta:
        model = Track
        fields = ("uuid", "url", "name", "number", "album")


class AlbumTrackSerializer(TrackSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="track-detail")

    class Meta:
        model = Track
        fields = ("uuid", "url", "name", "number")


class AlbumArtistSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="artist-detail")

    class Meta:
        model = Artist
        fields = ("uuid", "url", "name")


class AlbumSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="album-detail")
    artist = AlbumArtistSerializer()
    tracks = AlbumTrackSerializer(many=True)

    class Meta:
        model = Album
        fields = ("uuid", "url", "name", "year", "artist", "tracks")


class ArtistSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="artist-detail")
    albums_url = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ("uuid", "url", "name", "albums_url")

    def get_albums_url(self, artist):
        path = drf_reverse("album-list", request=self.context["request"])
        return furl(path).set({"artist_uuid": artist.uuid}).url


class PlaylistSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = UUIDHyperlinkedIdentityField(view_name="playlist-detail")
    tracks = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = ("uuid", "url", "name", "tracks")

    def get_tracks(self, obj):
        pts = obj.playlist_tracks.select_related("track__album__artist").order_by(
            "position"
        )
        return [TrackSerializer(pt.track, context=self.context).data for pt in pts]

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        if "tracks" in data:
            if not isinstance(data["tracks"], list):
                raise serializers.ValidationError({"tracks": "Expected a list."})
            tracks = []
            for val in data["tracks"]:
                try:
                    track = Track.objects.get(uuid=val)
                except (Track.DoesNotExist, ValueError):
                    raise serializers.ValidationError(
                        {"tracks": [f"Invalid track UUID: {val}"]}
                    )
                tracks.append(track)
            ret["tracks"] = tracks
        return ret

    def create(self, validated_data):
        tracks = validated_data.pop("tracks", [])
        with transaction.atomic():
            playlist = Playlist.objects.create(**validated_data)
            PlaylistTrack.objects.bulk_create(
                [
                    PlaylistTrack(playlist=playlist, track=track, position=i)
                    for i, track in enumerate(tracks, start=1)
                ]
            )
        return playlist

    def update(self, instance, validated_data):
        tracks = validated_data.pop("tracks", None)
        with transaction.atomic():
            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            instance.save()
            if tracks is not None:
                instance.playlist_tracks.all().delete()
                PlaylistTrack.objects.bulk_create(
                    [
                        PlaylistTrack(playlist=instance, track=track, position=i)
                        for i, track in enumerate(tracks, start=1)
                    ]
                )
        return instance
