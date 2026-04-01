import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView

from .forms import PlaylistForm, PlaylistTrackFormSet
from .models import Album, Artist, Playlist, Track

logger = logging.getLogger(__name__)

# ── Catalogue ─────────────────────────────────────────────────────────────────


class ArtistListView(ListView):
    model = Artist
    template_name = "grunge/artist_list.html"
    context_object_name = "artists"
    paginate_by = 24

    def get_queryset(self):
        qs = Artist.objects.annotate(
            album_count=Count("albums", distinct=True),
            track_count=Count("albums__tracks", distinct=True),
        ).order_by("name")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_q"] = self.request.GET.get("q", "")
        return context


class ArtistDetailView(DetailView):
    model = Artist
    template_name = "grunge/artist_detail.html"
    context_object_name = "artist"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Artist.objects.prefetch_related(
            Prefetch(
                "albums",
                queryset=Album.objects.annotate(track_count=Count("tracks")).order_by(
                    "year", "name"
                ),
            )
        )


class AlbumDetailView(DetailView):
    model = Album
    template_name = "grunge/album_detail.html"
    context_object_name = "album"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Album.objects.select_related("artist").prefetch_related(
            Prefetch("tracks", queryset=Track.objects.order_by("number"))
        )


class TrackListView(ListView):
    model = Track
    template_name = "grunge/track_list.html"
    context_object_name = "tracks"
    paginate_by = 50

    def get_queryset(self):
        qs = Track.objects.select_related("album__artist").order_by(
            "album__artist__name", "album__year", "album__name", "number"
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(album__name__icontains=q)
                | Q(album__artist__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_q"] = self.request.GET.get("q", "")
        return context


# ── Playlists ──────────────────────────────────────────────────────────────────


class PlaylistListView(ListView):
    model = Playlist
    template_name = "grunge/playlist_list.html"
    context_object_name = "playlists"
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(track_count=Count("playlist_tracks"))
            .order_by("name")
        )
        name = self.request.GET.get("name", "").strip()
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_name"] = self.request.GET.get("name", "")
        return context


class PlaylistDetailView(DetailView):
    model = Playlist
    template_name = "grunge/playlist_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("playlist_tracks__track__album__artist")
        )


def playlist_create(request):
    if request.method == "POST":
        form = PlaylistForm(request.POST)
        formset = PlaylistTrackFormSet(request.POST)
        form_ok = form.is_valid()
        formset_ok = formset.is_valid()
        if form_ok and formset_ok:
            with transaction.atomic():
                playlist = form.save()
                formset.instance = playlist
                _save_formset_with_positions(formset)
            messages.success(request, f"Playlist \u201c{playlist.name}\u201d created.")
            return redirect(playlist)
        if settings.DEBUG and not formset_ok:
            _log_playlist_formset_post(request, formset, "create")
    else:
        form = PlaylistForm()
        formset = PlaylistTrackFormSet()
    return render(
        request,
        "grunge/playlist_form.html",
        {"form": form, "formset": formset, "action": "Create"},
    )


def playlist_update(request, uuid):
    playlist = get_object_or_404(Playlist, uuid=uuid)
    if request.method == "POST":
        form = PlaylistForm(request.POST, instance=playlist)
        formset = PlaylistTrackFormSet(request.POST, instance=playlist)
        form_ok = form.is_valid()
        formset_ok = formset.is_valid()
        if form_ok and formset_ok:
            with transaction.atomic():
                form.save()
                _save_formset_with_positions(formset)
            messages.success(request, f"Playlist \u201c{playlist.name}\u201d updated.")
            return redirect(playlist)
        if settings.DEBUG and not formset_ok:
            _log_playlist_formset_post(request, formset, "update")
    else:
        form = PlaylistForm(instance=playlist)
        formset = PlaylistTrackFormSet(
            instance=playlist,
            queryset=playlist.playlist_tracks.select_related("track__album__artist"),
        )
    return render(
        request,
        "grunge/playlist_form.html",
        {"form": form, "formset": formset, "action": "Edit", "playlist": playlist},
    )


class PlaylistDeleteView(DeleteView):
    model = Playlist
    template_name = "grunge/playlist_confirm_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("playlist-list")

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f"Playlist \u201c{name}\u201d deleted.")
        return response


def _log_playlist_formset_post(request, formset, label):
    """Emit playlist_tracks POST + errors when DEBUG and validation fails."""
    keys = sorted(k for k in request.POST if k.startswith("playlist_tracks"))
    payload = {k: request.POST.get(k, "") for k in keys}
    logger.warning(
        "Playlist formset invalid (%s): errors=%s post=%s",
        label,
        formset.errors,
        payload,
    )


def _save_formset_with_positions(formset):
    """
    Save all non-deleted formset forms, assigning sequential positions (1-based)
    based on the visual order the forms were submitted in.

    Uses deleted_forms (available after is_valid()) rather than deleted_objects
    (which is only set after formset.save() is called).
    """
    # Delete removed rows first to avoid unique constraint conflicts
    for form in formset.deleted_forms:
        if form.instance.pk:
            form.instance.delete()

    # Respect drag order: each form's ORDER field (synced from DOM in JS).
    position = 1
    for form in formset.ordered_forms:
        if not form.cleaned_data:
            continue
        if form.cleaned_data.get("DELETE"):
            continue
        instance = form.save(commit=False)
        instance.playlist = formset.instance  # ensure FK is set for new playlists
        instance.position = position
        instance.save()
        position += 1
