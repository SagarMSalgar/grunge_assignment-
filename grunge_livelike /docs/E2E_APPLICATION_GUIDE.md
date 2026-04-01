# Grunge — End-to-End Application Guide

This document describes how the project is structured, how data flows from the database through Python to HTTP responses, and where each responsibility lives **with file paths and line numbers** as of the current codebase.

---

## 1. Purpose (README alignment)

- **Catalogue:** Browse artists, albums, and tracks (read-only HTML + read-only REST for those resources).
- **Playlists (fullstack goal):** Create, read, update, delete playlists via **Django views and templates**; tracks are **ordered** within a playlist; **Django admin** can browse and manage playlists.

The assignment README is at the repo root: `README.md`.

---

## 2. Stack & how to run

| Piece | Role |
|--------|------|
| Python 3.10+ | Runtime |
| Django 5.x | Web framework, ORM, admin, forms |
| Django REST Framework | API for artists / albums / tracks (`grunge/viewsets.py`, `grunge/serializers.py`) |
| SQLite (default) | Database (`db.sqlite3` when migrated locally; gitignored — see `.gitignore` 56) |
| Templates | Server-rendered UI under `grunge/templates/grunge/` |

**Entry points**

- `manage.py` — Django CLI (`DJANGO_SETTINGS_MODULE` → `grunge.settings`).
- `grunge/settings.py` — apps, DB, `INSTALLED_APPS`, feature flags:
  - `DJANGO_ADMIN_ENABLED` (lines 20–21, default True)
  - `DJANGO_API_ENABLED` (lines 21–22, default True)
- `grunge/urls.py` — URL routing (see §5).

**Standard commands** (from `README.md` / `Makefile`)

- `make ready` → `check`, `flake8`, `black --check`, `test --failfast` (`Makefile` 20, 10–12, 14–18).
- `python manage.py migrate` / `loaddata initial_data` — DB setup.

---

## 3. Database schema (ORM ↔ tables)

### 3.1 Conceptual model

```
Artist (UUIDModel)
  └── Album (FK artist)
        └── Track (FK album, unique per album+number)

Playlist (UUIDModel)
  └── PlaylistTrack (through)
        ├── FK → Playlist
        ├── FK → Track
        └── position (1-based order in playlist)

Playlist.tracks — M2M to Track **through** PlaylistTrack (`models.py` 91–96).
```

### 3.2 Source of truth in code

| Concept | File | Lines |
|--------|------|-------|
| `UUIDModel`, `UUIDManager` | `grunge/models.py` | 8–21 |
| `Artist` | `grunge/models.py` | 24–35 |
| `Album` | `grunge/models.py` | 38–58 |
| `Track` | `grunge/models.py` | 61–86 |
| `Playlist` | `grunge/models.py` | 89–105 |
| `PlaylistTrack` | `grunge/models.py` | 108–132 |
| Unique `(album, number)` on `Track` | `grunge/models.py` | 76–79 |
| Unique `(playlist, track)` on `PlaylistTrack` | `grunge/models.py` | 125–128 |
| Default ordering: playlist tracks by `position` | `grunge/models.py` | 123–124 |

### 3.3 Migration that creates playlist tables

File: `grunge/migrations/0003_playlist_playlisttrack.py`

| What | Lines |
|------|-------|
| Depends on `0002_…` | 9–11 |
| Create `Playlist` (`id`, `uuid`, `name`) | 14–40 |
| Create `PlaylistTrack` (`id`, `position`, `playlist_id`, `track_id`) | 41–79 |
| M2M `Playlist.tracks` through `PlaylistTrack` | 80–89 |
| `UniqueConstraint(playlist, track)` | 90–95 |

Applying migrations updates the **actual** DB schema to match these operations.

---

## 4. URL map → view → template

File: `grunge/urls.py`

### 4.1 Public HTML (non-admin)

| Path | Name | View | Lines |
|------|------|------|-------|
| `/` | — | Redirect → `/artists/` | 22 |
| `/artists/` | `artist-list` | `ArtistListView` | 24 |
| `/artists/<uuid>/` | `artist-detail` | `ArtistDetailView` | 25 |
| `/albums/<uuid>/` | `album-detail` | `AlbumDetailView` | 26 |
| `/tracks/` | `track-list` | `TrackListView` | 27 |
| `/playlists/` | `playlist-list` | `PlaylistListView` | 29 |
| `/playlists/new/` | `playlist-create` | `playlist_create` | 30 |
| `/playlists/<uuid>/` | `playlist-detail` | `PlaylistDetailView` | 31–35 |
| `/playlists/<uuid>/edit/` | `playlist-update` | `playlist_update` | 36 |
| `/playlists/<uuid>/delete/` | `playlist-delete` | `PlaylistDeleteView` | 37–41 |

Imports for playlist views: `grunge/urls.py` 7–17.

### 4.2 Admin & API (conditional)

| Condition | What gets mounted | Lines |
|-----------|-------------------|-------|
| `DJANGO_ADMIN_ENABLED` | `/admin/` | 44–47 |
| `DJANGO_API_ENABLED` | `/api/<version>/` + router for artists, albums, tracks **only** | 49–57 |

**Note:** There is **no** playlist `ViewSet` registered in `urls.py` 50–53; playlist CRUD for the fullstack track is **template-based only**.

---

## 5. Views layer (`grunge/views.py`)

### 5.1 Catalogue (read-only browsing)

| Class / area | Responsibility | Lines |
|--------------|----------------|-------|
| `ArtistListView` | Paginated artists + search `q`; annotate album/track counts | 19–38 |
| `ArtistDetailView` | Artist by `uuid`; prefetch albums + track counts | 41–56 |
| `AlbumDetailView` | Album by `uuid`; `select_related` artist; prefetch tracks | 59–69 |
| `TrackListView` | Paginated tracks + search; `select_related` album/artist | 72–94 |

### 5.2 Playlists

| Symbol | Responsibility | Lines |
|--------|----------------|-------|
| `PlaylistListView` | List playlists; `Count("playlist_tracks")`; filter `name` | 100–121 |
| `PlaylistDetailView` | Detail by `uuid`; `prefetch_related("playlist_tracks__track__album__artist")` | 124–135 |
| `playlist_create` | GET: empty `PlaylistForm` + `PlaylistTrackFormSet`. POST: validate both, atomic save playlist then `_save_formset_with_positions` | 138–160 |
| `playlist_update` | GET: bind forms to `playlist` + ordered queryset. POST: same as create but `instance=playlist` | 163–188 |
| `PlaylistDeleteView` | Delete playlist; redirect to `playlist-list`; success message | 191–202 |
| `_log_playlist_formset_post` | DEBUG-only logging when formset invalid | 205–214 |
| `_save_formset_with_positions` | Apply deletes from `deleted_forms`; then walk **`ordered_forms`** and set `position` 1..n | 217–241 |

**Important:** Save order uses `formset.ordered_forms` (`views.py` 232), which respects Django’s **`ORDER`** field on each inline form (see §6–§7). Positions are written to `PlaylistTrack.position` (`views.py` 237–240).

---

## 6. Forms layer (`grunge/forms.py`)

| Symbol | Role | Lines |
|--------|------|-------|
| `GroupedTrackChoiceField` | `ModelChoiceField` with dynamic **grouped** `choices` (by artist) for templates/labels | 11–29 |
| `PlaylistForm` | Edits `Playlist.name` only | 32–35 |
| `PlaylistTrackForm` | Edits `PlaylistTrack.track` via `HiddenInput`; `track` **required=False** at field level | 38–64 |
| `PlaylistTrackForm.clean` | If not `DELETE`, require `track` (manual validation) | 52–64 |
| `PlaylistTrackInlineFormSet` | After super `add_fields`, force `ORDER` widget to `HiddenInput` | 67–73 |
| `PlaylistTrackFormSet` | `inlineformset_factory`: `can_delete=True`, **`can_order=True`**, `extra=0` | 76–84 |

**Why `PlaylistTrackInlineFormSet`:** Django adds the `ORDER` field **after** `Form.__init__`, so hiding it must happen in `add_fields` (`forms.py` 67–73).

---

## 7. Playlist edit/create UI (`grunge/templates/grunge/playlist_form.html`)

The file is **~710 lines** (template + large `<script>` block). Logical sections:

| Section | Approx. lines | Purpose |
|---------|----------------|---------|
| `<style>` combobox / drag UI | ~7–122 | Visual styling |
| Breadcrumb, debug banner (`?playlist_debug=1`) | ~124–142 | Navigation / optional console debug |
| Form open, `management_form`, error summaries | ~144–168 | `formset` / per-row errors (hides row errors when `DELETE` checked) |
| Playlist name field | ~170–187 | `PlaylistForm` |
| Track formset card, `#formset-body` rows | ~189–283 | For each `formset` form: `hidden_fields` (includes `track` HiddenInput, `id`, `playlist`, **`ORDER`**), combobox, delete UI |
| Submit / Cancel | ~296–313 | POST |
| `#empty-form-tmpl` | ~316–364 | Clone source for “Add track” (includes `empty_form.hidden_fields`) |
| `{% block extra_js %}` IIFE | ~367–706 | Combobox, drag-and-drop, **reindex** (rename `playlist_tracks-N-*` by DOM order on submit / remove), **`syncOrderFromDom`** (sets `ORDER` 1..n), submit sync from label → hidden track |

**Client-side ordering contract**

1. **`ORDER` fields** (hidden) are set to **1, 2, 3, …** in **current DOM row order** (`syncOrderFromDom` — called on load, after drag, after remove, after add, and on submit after `reindex`).
2. On **submit**, **`reindex()`** rewrites `name`/`id` so prefixes are `0..n-1` in DOM order (suffix-based parsing avoids corrupting attributes).
3. Server reads POST into the formset; **`ordered_forms`** sorts by `ORDER`; `_save_formset_with_positions` writes **`position`** accordingly.

---

## 8. Playlist read UI

| Template | Used by | Role |
|----------|---------|------|
| `grunge/playlist_list.html` | `PlaylistListView` | Lists playlists + search |
| `grunge/playlist_detail.html` | `PlaylistDetailView` | Shows `playlist.playlist_tracks.all` — respects `PlaylistTrack.Meta.ordering` (`position`) |
| `grunge/playlist_confirm_delete.html` | `PlaylistDeleteView` | Confirm delete |

Detail template reference: `playlist_detail.html` uses `{% for pt in tracks %}` with `pt.position` (see file ~62–72).

---

## 9. Django admin (`grunge/admin.py`)

Playlist-related admin:

| Piece | Lines | Behavior |
|-------|-------|----------|
| `PlaylistTrackInline` | 241–246 | Tabular inline: `position`, `track`; `autocomplete_fields` for `track` |
| `PlaylistAdmin` | 249–275 | Registered model; `list_display`, `search_fields`; `track_count` via `Count` annotation (`get_queryset` 265–266); link to public playlist detail (`playlist_view_link` 272–275) |

Imports include `Playlist`, `PlaylistTrack` (`admin.py` 10).

---

## 10. REST API (what exists)

- Router registration: `grunge/urls.py` 50–53 — **`artists`**, **`albums`**, **`tracks`** only.
- **No** playlist endpoints in the router; serializers/viewsets for playlists are **not** in the shipped assessment layout described here.

If the role were **backend** per README, playlist API + `tests/test_playlists.py` would be additional scope.

---

## 11. Tests

| File | Notes |
|------|--------|
| `grunge/tests/test_artists.py`, `test_albums.py`, `test_tracks.py` | API tests for catalogue |
| `grunge/tests/test_playlists.py` | All methods still **`@skip`** — placeholders only (lines 10–39); **does not exercise** template playlist CRUD |

Running tests: `python manage.py test` or `make ready` (`Makefile` 14–20).

---

## 12. End-to-end: one “edit playlist + reorder + save” flow

1. **GET** `/playlists/<uuid>/edit/` → `playlist_update` (`views.py` 163–188): loads `Playlist`, builds `PlaylistTrackFormSet` with queryset ordered by `position` and `select_related` for tracks.
2. Browser renders `playlist_form.html`: each row has hidden `id`, `playlist`, `track`, **`ORDER`**, optional `DELETE`, plus combobox UI.
3. User drags rows → JS updates **`ORDER`** only (no prefix rename during drag); optional `?playlist_debug=1` logs state.
4. User clicks **Save** → JS runs `reindex()` then `syncOrderFromDom()`, then syncs visible track label into the hidden `track` input if needed, then POST.
5. **POST** → `playlist_update` (`views.py` 165–177): `PlaylistForm` + `PlaylistTrackFormSet` bound; both `is_valid()`; `_save_formset_with_positions` (`views.py` 217–241):
   - Deletes instances for forms marked `DELETE` (`226–228`).
   - Iterates `ordered_forms` (`232`): assigns `position = 1, 2, …` in **ORDER** order (`237–240`).
6. Redirect to `playlist.get_absolute_url()` → detail view lists `playlist_tracks` ordered by **`position`** in the DB.

---

## 13. Logging & debug

| Mechanism | Where |
|-----------|--------|
| App logger `grunge` | `grunge/settings.py` 41–48 |
| Invalid playlist formset POST (DEBUG) | `views.py` 205–214, called from 151–152, 176–177 |
| Browser: `?playlist_debug=1` or `localStorage GRUNGE_PLAYLIST_DEBUG` | `playlist_form.html` (see §7) |

---

## 14. File index (quick reference)

| Area | Primary files |
|------|----------------|
| Models | `grunge/models.py` |
| Migrations | `grunge/migrations/0003_playlist_playlisttrack.py` (+ earlier catalogue migrations) |
| Forms / formset | `grunge/forms.py` |
| HTTP views | `grunge/views.py` |
| Routes | `grunge/urls.py` |
| Settings | `grunge/settings.py` |
| Admin | `grunge/admin.py` |
| Playlist UI | `grunge/templates/grunge/playlist_*.html` |
| API (catalogue) | `grunge/viewsets.py`, `grunge/serializers.py` |
| Tooling | `Makefile`, `requirements.txt`, `README.md` |

---

*Line numbers refer to the repository state when this guide was generated; if you edit files, line numbers may shift—grep or your editor’s symbol search remains the source of truth.*
