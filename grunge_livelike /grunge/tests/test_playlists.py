from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse as drf_reverse

from . import BaseAPITestCase


class PlaylistTests(BaseAPITestCase):
    def setUp(self):
        # Fetch two known tracks from the fixture for use in tests
        track_url = drf_reverse("track-list", kwargs={"version": self.version})
        r = self.client.get(track_url)
        results = r.data["results"]
        self.track_uuid_1 = results[0]["uuid"]
        self.track_uuid_2 = results[1]["uuid"]
        self.track_uuid_3 = results[2]["uuid"]

    def _list_url(self):
        return drf_reverse("playlist-list", kwargs={"version": self.version})

    def _detail_url(self, uuid):
        return drf_reverse(
            "playlist-detail", kwargs={"version": self.version, "uuid": uuid}
        )

    def _create(self, name="Test Playlist", tracks=None):
        data = {"name": name}
        if tracks is not None:
            data["tracks"] = [str(t) for t in tracks]
        return self.client.post(self._list_url(), data, format="json")

    def test_list_playlists(self):
        # No playlists initially
        r = self.client.get(self._list_url())
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 0)

        # Create one and verify count increases
        self._create("Alpha")
        r = self.client.get(self._list_url())
        self.assertEqual(r.data["count"], 1)

    def test_search_playlists(self):
        self._create("Grunge Classics")
        self._create("Sunday Morning Mix")

        url = furl(self._list_url()).set({"name": "Grunge"}).url
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["name"], "Grunge Classics")

    def test_get_playlist(self):
        create_r = self._create("My Playlist", tracks=[self.track_uuid_1])
        self.assertEqual(create_r.status_code, status.HTTP_201_CREATED)
        uuid = create_r.data["uuid"]

        r = self.client.get(self._detail_url(uuid))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], "My Playlist")
        self.assertEqual(len(r.data["tracks"]), 1)
        self.assertEqual(r.data["tracks"][0]["uuid"], self.track_uuid_1)

    def test_create_playlist(self):
        # Create with 0 tracks
        r = self._create("Empty Playlist", tracks=[])
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["name"], "Empty Playlist")
        self.assertEqual(len(r.data["tracks"]), 0)

        # Create with ordered tracks
        r = self._create("Full Playlist", tracks=[self.track_uuid_1, self.track_uuid_2])
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(r.data["tracks"]), 2)
        self.assertEqual(r.data["tracks"][0]["uuid"], self.track_uuid_1)
        self.assertEqual(r.data["tracks"][1]["uuid"], self.track_uuid_2)

    def test_update_playlist(self):
        r = self._create("Original", tracks=[self.track_uuid_1, self.track_uuid_2])
        uuid = r.data["uuid"]

        # Rename
        r = self.client.patch(
            self._detail_url(uuid), {"name": "Updated"}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], "Updated")

        # Re-order tracks
        r = self.client.patch(
            self._detail_url(uuid),
            {"tracks": [str(self.track_uuid_2), str(self.track_uuid_1)]},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["tracks"][0]["uuid"], self.track_uuid_2)
        self.assertEqual(r.data["tracks"][1]["uuid"], self.track_uuid_1)

        # Add a third track
        r = self.client.patch(
            self._detail_url(uuid),
            {
                "tracks": [
                    str(self.track_uuid_1),
                    str(self.track_uuid_2),
                    str(self.track_uuid_3),
                ]
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data["tracks"]), 3)

        # Remove all tracks
        r = self.client.patch(self._detail_url(uuid), {"tracks": []}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data["tracks"]), 0)

    def test_delete_playlist(self):
        r = self._create("To Delete")
        uuid = r.data["uuid"]

        r = self.client.delete(self._detail_url(uuid))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

        r = self.client.get(self._detail_url(uuid))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
