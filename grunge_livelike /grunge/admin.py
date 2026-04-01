from django.conf import settings
from django.contrib import admin
from django.db.models import Count, F
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from furl import furl
from rest_framework.reverse import reverse as drf_reverse

from .models import Album, Artist, Playlist, PlaylistTrack, Track


def get_api_url(obj, view="detail", params=None, title=None, request=None):
    path = drf_reverse(
        f"{obj._meta.model_name}-{view}",
        kwargs={
            "uuid": obj.uuid,
            "version": settings.REST_FRAMEWORK["DEFAULT_VERSION"],
        },
        request=request,
    )

    if params:
        path = furl(path).set(params).url

    return format_html('<a href="{0}" title="{1}">{1}</a>', path, title or str(obj))


def get_admin_url(obj, view="change", params=None, title=None):
    path = reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_{view}",
        kwargs={"object_id": obj.pk} if view == "change" else {},
    )

    if params:
        path = furl(path).set(params).url

    return format_html('<a href="{0}" title="{1}">{1}</a>', path, title or str(obj))


class ArtistDecadeActiveListFilter(admin.SimpleListFilter):

    title = _("decade active")
    parameter_name = "decade_active"

    def lookups(self, request, model_admin):
        return (
            ("1980", _("1980s")),
            ("1990", _("1990s")),
            ("2000", _("2000s")),
            ("2010", _("2010s")),
            ("2020", _("2020s")),
        )

    def queryset(self, request, queryset):
        value = self.value()

        if not value:
            return queryset

        try:
            year_since = int(value)
            year_until = year_since + 10
        except ValueError:
            return queryset

        return queryset.filter(
            albums__year__gte=year_since, albums__year__lt=year_until
        )


class ArtistAlbumInline(admin.TabularInline):
    model = Album
    fields = ("name", "year", "album_admin_link", "tracks_admin_link")
    readonly_fields = ("album_admin_link", "tracks_admin_link")
    extra = 0

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(track_count=Count("tracks"))

    @admin.display(description=_("Album"))
    def album_admin_link(self, album):
        return get_admin_url(album)

    @admin.display(description=_("Tracks"))
    def tracks_admin_link(self, album):
        return get_admin_url(
            Track,
            view="changelist",
            params={"album": album.pk},
            title=album.track_count,
        )


class AlbumTrackInline(admin.TabularInline):
    model = Track
    fields = ("number", "name")
    extra = 0


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "albums_admin_link")
    list_filter = (ArtistDecadeActiveListFilter,)
    fields = ("name", "uuid", "albums_admin_link", "artist_api_link")
    readonly_fields = ("uuid", "albums_admin_link", "artist_api_link")
    search_fields = ("uuid", "name")
    inlines = (ArtistAlbumInline,)

    def get_queryset(self, request):
        self.request = request
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("albums").annotate(
            album_count=Count("albums", distinct=True)
        )

    @admin.display(description=_("Albums"), ordering="album_count")
    def albums_admin_link(self, artist):
        return get_admin_url(
            Album,
            view="changelist",
            params={"artist": artist.pk},
            title=artist.album_count or "0",
        )

    @admin.display(description=_("API"))
    def artist_api_link(self, artist):
        return get_api_url(artist, request=self.request)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "artist_admin_link", "album_year", "tracks_admin_link")
    list_filter = ("year",)
    search_fields = ("uuid", "name", "artist__name")
    fields = (
        "name",
        "year",
        "uuid",
        "artist_admin_link",
        "tracks_admin_link",
        "album_api_link",
    )
    readonly_fields = (
        "uuid",
        "tracks_admin_link",
        "artist_admin_link",
        "album_api_link",
    )
    list_select_related = ("artist",)
    inlines = (AlbumTrackInline,)

    def has_add_permission(self, request):
        # Add albums from the Artist album inline
        return False

    def get_queryset(self, request):
        self.request = request
        queryset = super().get_queryset(request)
        return queryset.annotate(track_count=Count("tracks"))

    @admin.display(description=_("Year"), ordering="year")
    def album_year(self, album):
        return get_admin_url(
            Album, view="changelist", params={"year": album.year}, title=album.year
        )

    @admin.display(description=_("Artist"), ordering="artist__name")
    def artist_admin_link(self, album):
        return get_admin_url(album.artist)

    @admin.display(description=_("Tracks"), ordering="track_count")
    def tracks_admin_link(self, album):
        return get_admin_url(
            Track,
            view="changelist",
            params={"album": album.pk},
            title=album.track_count or "0",
        )

    @admin.display(description=_("API"))
    def album_api_link(self, album):
        return get_api_url(album, request=self.request)


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("name", "artist_admin_link", "album_admin_link", "album_year")
    list_filter = ("album__year",)
    search_fields = ("uuid", "name", "album__name", "album__artist__name")
    fields = (
        "name",
        "uuid",
        "artist_admin_link",
        "album_admin_link",
        "album_year",
        "track_api_link",
    )
    readonly_fields = (
        "uuid",
        "artist_admin_link",
        "album_admin_link",
        "album_year",
        "track_api_link",
    )
    list_select_related = ("album", "album__artist")
    ordering = ("name", "album__artist__name", "album__name")

    def has_add_permission(self, request):
        # Add tracks from the Album track inline
        return False

    def get_queryset(self, request):
        self.request = request
        queryset = super().get_queryset(request)
        return queryset.annotate(album_year=F("album__year"))

    @admin.display(description=_("Album"), ordering="album__name")
    def album_admin_link(self, track):
        return get_admin_url(track.album)

    @admin.display(description=_("Artist"), ordering="album__artist__name")
    def artist_admin_link(self, track):
        return get_admin_url(track.album.artist)

    @admin.display(description=_("Year"), ordering="album__year")
    def album_year(self, track):
        return get_admin_url(
            Track,
            view="changelist",
            params={"album__year": track.album_year},
            title=track.album_year,
        )

    @admin.display(description=_("API"))
    def track_api_link(self, track):
        return get_api_url(track, request=self.request)


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    fields = ("position", "track")
    ordering = ("position",)
    extra = 1
    autocomplete_fields = ("track",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "track_count", "uuid", "playlist_view_link")
    search_fields = ("uuid", "name")
    inlines = (PlaylistTrackInline,)

    def get_fields(self, request, obj=None):
        if obj:
            return ("name", "uuid", "playlist_view_link")
        return ("name",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("uuid", "playlist_view_link")
        return ()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(track_count=Count("tracks"))

    @admin.display(description=_("Tracks"), ordering="track_count")
    def track_count(self, playlist):
        return playlist.track_count

    @admin.display(description=_("View on site"))
    def playlist_view_link(self, playlist):
        url = reverse("playlist-detail", kwargs={"uuid": playlist.uuid})
        return format_html('<a href="{}" target="_blank">&#8599; Open</a>', url)
