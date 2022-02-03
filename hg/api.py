from collections import defaultdict
from functools import wraps
from typing import Dict, List, Optional, Tuple, TypeVar, Union, overload

import slugid
from higlass_schema import CombinedTrack as _CombinedTrack
from higlass_schema import Data, Domain
from higlass_schema import EnumTrack as _EnumTrack
from higlass_schema import EnumTrackType
from higlass_schema import HeatmapTrack as _HeatmapTrack
from higlass_schema import (
    IndependentViewportProjectionTrack as _IndependentViewportProjectionTrack,
)
from higlass_schema import Layout, LocationLocks, Lock
from higlass_schema import Track as _Track
from higlass_schema import Tracks, ValueScaleLock, ValueScaleLocks
from higlass_schema import View as _View
from higlass_schema import Viewconf as _Viewconf
from higlass_schema import ZoomLocks
from pydantic import BaseModel as PydanticBaseModel
from typing_extensions import Literal

from .display import renderers

TrackType = Union[EnumTrackType, Literal["heatmap"]]
TrackPosition = Literal["center", "top", "left", "bottom", "center", "whole", "gallery"]

_track_default_position: Dict[str, TrackPosition] = {
    "2d-rectangle-domains": "center",
    "bedlike": "top",
    "horizontal-bar": "top",
    "horizontal-chromosome-labels": "top",
    "chromosome-labels": "top",
    "horizontal-gene-annotations": "top",
    "horizontal-heatmap": "top",
    "horizontal-1d-heatmap": "top",
    "horizontal-line": "top",
    "horizontal-multivec": "top",
    "bar": "top",
    "chromosome-labels": "top",
    "gene-annotations": "top",
    "heatmap": "top",
    "1d-heatmap": "top",
    "line": "top",
    "horizontal-multivec": "top",
    "heatmap": "center",
    "left-axis": "left",
    "osm-tiles": "center",
    "top-axis": "top",
    "viewport-projection-center": "center",
    "viewport-projection-horizontal": "top",
}

# Switch pydantic defaults
class BaseModel(PydanticBaseModel):
    class Config:
        # wether __setattr__ should perform validation
        validate_assignment = True

    # nice repr if printing with rich
    def __rich_repr__(self):
        return self.__iter__()

    # Omit fields which are None by default.
    @wraps(PydanticBaseModel.dict)
    def dict(self, exclude_none: bool = True, **kwargs):
        return super().dict(exclude_none=exclude_none, **kwargs)

    # Omit fields which are None by default.
    @wraps(PydanticBaseModel.json)
    def json(self, exclude_none: bool = True, **kwargs):
        return super().json(exclude_none=exclude_none, **kwargs)


ModelT = TypeVar("ModelT", bound=PydanticBaseModel)


def _copy_unique(model: ModelT) -> ModelT:
    copy = model.__class__(**model.dict())
    if hasattr(copy, "uid"):
        setattr(copy, "uid", str(slugid.nice()))
    return copy


T = TypeVar("T")


def _ensure_list(x: Union[None, T, List[T]]) -> List[T]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


class _PropertiesMixin:
    def properties(self: ModelT, inplace: bool = False, **fields) -> ModelT:  # type: ignore
        model = self if inplace else _copy_unique(self)
        for k, v in fields.items():
            setattr(model, k, v)
        return model


TrackT = TypeVar("TrackT", bound=_Track)


class _OptionsMixin:
    def opts(self: TrackT, inplace: bool = False, **options) -> TrackT:  # type: ignore
        track = self if inplace else _copy_unique(self)
        if track.options is None:
            track.options = {}
        track.options.update(options)
        return track


class EnumTrack(_EnumTrack, _OptionsMixin, _PropertiesMixin):
    ...


class HeatmapTrack(_HeatmapTrack, _OptionsMixin, _PropertiesMixin):
    ...


class IndependentViewportProjectionTrack(
    _IndependentViewportProjectionTrack, _OptionsMixin, _PropertiesMixin
):
    ...


class CombinedTrack(_CombinedTrack, _OptionsMixin, _PropertiesMixin):
    ...


Track = Union[
    EnumTrack,
    HeatmapTrack,
    IndependentViewportProjectionTrack,
    CombinedTrack,
]


class View(_View[Track], _PropertiesMixin):
    def domain(
        self,
        x: Optional[Domain] = None,
        y: Optional[Domain] = None,
        inplace: bool = False,
    ):
        view = self if inplace else _copy_unique(self)
        if x is not None:
            view.initialXDomain = x
        if y is not None:
            view.initialYDomain = y
        return view

    # TODO: better name? adjust_layout, resize
    def move(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        inplace: bool = False,
    ):
        view = self if inplace else _copy_unique(self)
        if x is not None:
            view.layout.x = x
        if y is not None:
            view.layout.y = y
        if width is not None:
            view.layout.w = width
        if height is not None:
            view.layout.h = height
        return view


class Viewconf(_Viewconf[View], _PropertiesMixin):
    def _repr_mimebundle_(self, include=None, exclude=None):
        renderer = renderers.get()
        return renderer(self.json())

    def display(self):
        """Render top-level chart using IPython.display."""
        from IPython.display import display

        display(self)

    def properties(self, inplace: bool = False, **kwargs):
        conf = self if inplace else _copy_unique(self)
        for k, v in kwargs.items():
            setattr(conf, k, v)
        return conf

    def locks(
        self,
        *locks: Union[Lock, ValueScaleLock],
        zoom: Optional[Union[List[Lock], Lock]] = None,
        location: Optional[Union[List[Lock], Lock]] = None,
        value_scale: Optional[Union[List[ValueScaleLock], ValueScaleLock]] = None,
        inplace: bool = False,
    ):
        conf = self if inplace else _copy_unique(self)

        zoom = _ensure_list(zoom)
        location = _ensure_list(location)
        value_scale = _ensure_list(value_scale)

        shared_locks: List[Lock] = []
        for lock in locks:
            if isinstance(lock, Lock):
                shared_locks.append(lock)
            else:
                value_scale.append(lock)

        zoom.extend(shared_locks)
        location.extend(shared_locks)

        if conf.zoomLocks is None:
            conf.zoomLocks = ZoomLocks()

        for lock in zoom:
            assert isinstance(lock.uid, str)
            conf.zoomLocks.locksDict[lock.uid] = lock
            for vuid, _ in lock:
                conf.zoomLocks.locksByViewUid[vuid] = lock.uid

        if conf.locationLocks is None:
            conf.locationLocks = LocationLocks()

        for lock in location:
            assert isinstance(lock.uid, str)
            conf.locationLocks.locksDict[lock.uid] = lock
            for vuid, _ in lock:
                conf.locationLocks.locksByViewUid[vuid] = lock.uid

        if conf.valueScaleLocks is None:
            conf.valueScaleLocks = ValueScaleLocks()

        for lock in value_scale:
            assert isinstance(lock.uid, str)
            conf.valueScaleLocks.locksDict[lock.uid] = lock
            for vuid, _ in lock:
                conf.valueScaleLocks.locksByViewUid[vuid] = lock.uid

        return conf


def track(
    type_: TrackType,
    uid: Optional[str] = None,
    fromViewUid: Optional[str] = None,
    **kwargs,
) -> Track:
    if uid is None:
        uid = str(slugid.nice())

    if (
        type_
        in {
            "viewport-projection-horizontal",
            "viewport-projection-vertical",
            "viewport-projection-center",
        }
        and fromViewUid is None
    ):
        return IndependentViewportProjectionTrack(
            type=type_, uid=uid, fromViewUid=fromViewUid, **kwargs  # type: ignore
        )

    if type_ == "heatmap":
        return HeatmapTrack(type=type_, uid=uid, **kwargs)

    return EnumTrack(type=type_, uid=uid, **kwargs)


def view(
    *_tracks: Union[
        Union[Track, _Track],
        Tracks,
        Tuple[Track, TrackPosition],
    ],
    x: int = 0,
    y: int = 0,
    width: int = 12,
    height: int = 6,
    tracks: Optional[Tracks] = None,
    layout: Optional[Layout] = None,
    uid: Optional[str] = None,
    **kwargs,
) -> View:

    if layout is None:
        layout = Layout(x=x, y=y, w=width, h=height)
    else:
        layout = Layout(**layout.dict())

    if tracks is None:
        data = defaultdict(list)
    else:
        data = defaultdict(list, tracks.dict())

    for track in _tracks:
        if isinstance(track, Tracks):
            track = track.dict()
            for position, track_list in track.items():
                data[position].extend(track_list)
        else:
            if isinstance(track, tuple):
                track, position = track
            else:
                if track.type is None:
                    raise ValueError("No default track type")
                position = _track_default_position[track.type]
            data[position].append(track)

    if uid is None:
        uid = str(slugid.nice())

    return View(
        layout=layout,
        tracks=Tracks(**data),
        uid=uid,
        **kwargs,
    )


def combine(t1: Track, t2: Track, uid: Optional[str] = None, **kwargs) -> CombinedTrack:
    if uid is None:
        uid = str(slugid.nice())

    if isinstance(t1, CombinedTrack):
        copy = CombinedTrack(**t1.dict())
        copy.contents.append(t2.__class__(**t2.dict()))
        for key, val in kwargs.items():
            setattr(copy, key, val)
        return copy

    return CombinedTrack(
        type="combined",
        uid=uid,
        contents=[track.__class__(**track.dict()) for track in (t1, t2)],
        **kwargs,
    )


T = TypeVar("T", bound=Union[EnumTrack, HeatmapTrack])


def divide(t1: T, t2: T, **kwargs) -> T:
    assert t1.type == t2.type, "divided tracks must be same type"
    assert isinstance(t1.tilesetUid, str)
    assert isinstance(t1.server, str)

    assert isinstance(t2.tilesetUid, str)
    assert isinstance(t2.server, str)

    copy = t1.opts()  # copy first track with new uid
    copy.tilesetUid = None
    copy.server = None
    copy.data = Data(
        type="divided",
        children=[
            {
                "tilesetUid": track.tilesetUid,
                "server": track.server,
            }
            for track in (t1, t2)
        ],
    )
    # overrides
    for key, val in kwargs.items():
        setattr(copy, key, val)
    return copy


def project(
    position: Literal["center", "top", "bottom", "left", "right"],
    view: Optional[View] = None,
    **kwargs,
):
    if view is None:
        fromViewUid = None
    else:
        assert isinstance(view.uid, str)
        fromViewUid = view.uid

    if position == "center":
        track_type = "viewport-projection-center"
    elif position == "top" or position == "bottom":
        track_type = "viewport-projection-horizontal"
    elif position == "left" or position == "right":
        track_type = "viewport-projection-vertical"
    else:
        raise ValueError("Not possible")

    return track(type_=track_type, fromViewUid=fromViewUid, **kwargs)


def viewconf(
    *_views: View,
    views: Optional[List[View]] = None,
    trackSourceServers: Optional[List[str]] = None,
    editable: bool = True,
    exportViewUrl: str = "http://higlass.io/api/v1/viewconfs",
    **kwargs,
):
    views = [] if views is None else [View(**v.dict()) for v in views]

    for view in _views:
        views.append(View(**view.dict()))

    if trackSourceServers is None:
        trackSourceServers = ["http://higlass.io/api/v1"]

    return Viewconf(
        views=views,
        editable=editable,
        exportViewUrl=exportViewUrl,
        trackSourceServers=trackSourceServers,
        **kwargs,
    )


@overload
def lock(*views: View, **kwargs) -> Lock:
    ...


@overload
def lock(*pairs: Tuple[View, Track], **kwargs) -> ValueScaleLock:
    ...


def lock(*data, **kwargs):
    assert len(data) >= 1
    uid = str(slugid.nice())
    if isinstance(data[0], View):
        lck = Lock(uid=uid, **kwargs)
        for view in data:
            assert isinstance(view.uid, str)
            setattr(lck, view.uid, (1, 1, 1))
        return lck
    else:
        lck = ValueScaleLock(uid=uid, **kwargs)
        for view, track in data:
            assert isinstance(view.uid, str)
            assert isinstance(track.uid, str)
            vtuid = f"{view.uid}.{track.uid}"
            setattr(lck, vtuid, {"track": track.uid, "view": view.uid})
        return lck
