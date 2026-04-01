from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    AlbumDetailView,
    ArtistDetailView,
    ArtistListView,
    PlaylistDeleteView,
    PlaylistDetailView,
    PlaylistListView,
    TrackListView,
    playlist_create,
    playlist_update,
)
from .viewsets import AlbumViewSet, ArtistViewSet, PlaylistViewSet, TrackViewSet

# Root always redirects to the app's home page
urlpatterns = [
    re_path(r"^$", RedirectView.as_view(url="/artists/", permanent=False)),
    # Catalogue (read-only browsing)
    path("artists/", ArtistListView.as_view(), name="artist-list"),
    path("artists/<uuid:uuid>/", ArtistDetailView.as_view(), name="artist-detail"),
    path("albums/<uuid:uuid>/", AlbumDetailView.as_view(), name="album-detail"),
    path("tracks/", TrackListView.as_view(), name="track-list"),
    # Playlists (full CRUD)
    path("playlists/", PlaylistListView.as_view(), name="playlist-list"),
    path("playlists/new/", playlist_create, name="playlist-create"),
    path(
        "playlists/<uuid:uuid>/",
        PlaylistDetailView.as_view(),
        name="playlist-detail",
    ),
    path("playlists/<uuid:uuid>/edit/", playlist_update, name="playlist-update"),
    path(
        "playlists/<uuid:uuid>/delete/",
        PlaylistDeleteView.as_view(),
        name="playlist-delete",
    ),
]

if settings.DJANGO_ADMIN_ENABLED:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]

if settings.DJANGO_API_ENABLED:
    api_router = DefaultRouter(trailing_slash=False)
    api_router.register("artists", ArtistViewSet)
    api_router.register("albums", AlbumViewSet)
    api_router.register("tracks", TrackViewSet)
    api_router.register("playlists", PlaylistViewSet, basename="playlist")

    urlpatterns += [
        path("api/<version>/", include(api_router.urls)),
    ]
