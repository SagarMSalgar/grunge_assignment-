from uuid import UUID

from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse as drf_reverse

from . import BaseAPITestCase


class TrackTests(BaseAPITestCase):
    def setUp(self):
        self.track_name = "Last Exit"
        self.track_uuid = UUID("b3083319-47a9-40ed-a4e0-a79d050d9df7")
        self.album_uuid = UUID("b4fee0db-0c93-4470-96b3-cebd158033a0")

    def test_list_tracks(self):
        url = drf_reverse("track-list", kwargs={"version": self.version})
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 3695)

    def test_search_tracks(self):
        url = drf_reverse("track-list", kwargs={"version": self.version})
        url = furl(url).set({"name": self.track_name}).url
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 4)
        self.assertEqual(r.data["results"][0]["uuid"], self.track_uuid)

    def test_get_track(self):
        url = drf_reverse(
            "track-detail", kwargs={"version": self.version, "uuid": self.track_uuid}
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], self.track_name)
        self.assertEqual(r.data["album"]["uuid"], self.album_uuid)
