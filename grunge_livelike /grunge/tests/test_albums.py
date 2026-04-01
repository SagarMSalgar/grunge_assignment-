from uuid import UUID

from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse as drf_reverse

from . import BaseAPITestCase


class AlbumTests(BaseAPITestCase):
    def setUp(self):
        self.album_name = "Vitalogy"
        self.album_uuid = UUID("b4fee0db-0c93-4470-96b3-cebd158033a0")
        self.artist_uuid = UUID("9e52205f-9927-4eff-b132-ce10c6f3e0b1")

    def test_list_albums(self):
        url = drf_reverse("album-list", kwargs={"version": self.version})
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 291)

    def test_search_albums(self):
        url = drf_reverse("album-list", kwargs={"version": self.version})
        url = furl(url).set({"name": self.album_name}).url
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 3)
        self.assertEqual(r.data["results"][0]["uuid"], self.album_uuid)
        self.assertEqual(r.data["results"][0]["artist"]["uuid"], self.artist_uuid)

    def test_get_album(self):
        url = drf_reverse(
            "album-detail", kwargs={"version": self.version, "uuid": self.album_uuid}
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], self.album_name)
        self.assertEqual(r.data["artist"]["uuid"], self.artist_uuid)
