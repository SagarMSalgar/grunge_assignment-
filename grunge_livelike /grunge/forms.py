from itertools import groupby

from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet

from .models import Playlist, PlaylistTrack, Track


class GroupedTrackChoiceField(forms.ModelChoiceField):
    """
    Renders tracks grouped by artist as <optgroup> elements.
    Each option shows: Album — #. Track Name
    """

    @property
    def choices(self):
        yield ("", "\u2014 Select a track \u2014")
        qs = self.queryset.order_by("album__artist__name", "album__name", "number")
        for artist_name, tracks in groupby(qs, key=lambda t: t.album.artist.name):
            group = [
                (t.pk, f"{t.album.name} \u2014 {t.number}. {t.name}") for t in tracks
            ]
            yield (artist_name, group)

    @choices.setter
    def choices(self, value):
        pass  # Django internals call this; grouped choices are generated dynamically


class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ("name",)


class PlaylistTrackForm(forms.ModelForm):
    # required=False: rows marked DELETE skip track validation (see clean()).
    # HiddenInput: one Django-rendered control (combobox in template mirrors into it).
    track = GroupedTrackChoiceField(
        queryset=Track.objects.select_related("album", "album__artist"),
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = PlaylistTrack
        fields = ("track",)
        # position is excluded — assigned server-side by _save_formset_with_positions

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("DELETE"):
            return cleaned_data
        if cleaned_data.get("track") is None:
            self.add_error(
                "track",
                ValidationError(
                    self.fields["track"].error_messages["required"],
                    code="required",
                ),
            )
        return cleaned_data


class PlaylistTrackInlineFormSet(BaseInlineFormSet):
    """ORDER is added after Form.__init__; hide it here (see add_fields on BaseFormSet)."""

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "ORDER" in form.fields:
            form.fields["ORDER"].widget = forms.HiddenInput()


PlaylistTrackFormSet = inlineformset_factory(
    Playlist,
    PlaylistTrack,
    form=PlaylistTrackForm,
    formset=PlaylistTrackInlineFormSet,
    extra=0,
    can_delete=True,
    can_order=True,
)
