import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("grunge", "0002_alter_album_id_alter_artist_id_alter_track_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Playlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, unique=True, verbose_name="UUID"
                    ),
                ),
                (
                    "name",
                    models.CharField(help_text="The playlist name", max_length=100),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="PlaylistTrack",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "position",
                    models.PositiveIntegerField(
                        help_text="Position of the track in the playlist (1-based)"
                    ),
                ),
                (
                    "playlist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="playlist_tracks",
                        to="grunge.playlist",
                    ),
                ),
                (
                    "track",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="playlist_tracks",
                        to="grunge.track",
                    ),
                ),
            ],
            options={
                "ordering": ("position",),
            },
        ),
        migrations.AddField(
            model_name="playlist",
            name="tracks",
            field=models.ManyToManyField(
                blank=True,
                related_name="playlists",
                through="grunge.PlaylistTrack",
                to="grunge.track",
            ),
        ),
        migrations.AddConstraint(
            model_name="playlisttrack",
            constraint=models.UniqueConstraint(
                fields=("playlist", "track"), name="unique_playlist_track"
            ),
        ),
    ]
