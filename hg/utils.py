from __future__ import annotations

import itertools
import uuid
from collections import OrderedDict
from operator import itemgetter
from typing import Dict, Iterable, List, Optional, Tuple, TypeVar, Union

import higlass_schema as hgs
from pydantic import BaseModel
from typing_extensions import Literal

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)

TrackType = Union[hgs.EnumTrackType, Literal["heatmap"]]
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

_datatype_default_track = {
    "2d-rectangle-domains": "2d-rectangle-domains",
    "bedlike": "bedlike",
    "chromsizes": "horizontal-chromosome-labels",
    "gene-annotations": "horizontal-gene-annotations",
    "matrix": "heatmap",
    "vector": "horizontal-bar",
    "multivec": "horizontal-multivec",
}


def uid():
    return str(uuid.uuid4())


def get_default_track_position(track_type: str) -> Optional[TrackPosition]:
    return _track_default_position.get(track_type, None)


def ensure_list(x: Union[None, T, List[T]]) -> List[T]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def copy_unique(model: ModelT) -> ModelT:
    """Creates a deep copy of a pydantic BaseModel with new UID"""
    copy = model.__class__(**model.dict())
    if hasattr(copy, "uid"):
        setattr(copy, "uid", uid())
    return copy


ViewInterval = Tuple[int, int]
GenomicRegion = Tuple[str, int, int]


def overlap(a: ViewInterval, b: ViewInterval) -> bool:
    return a[1] >= b[0] and a[0] <= b[1]


class GenomicScale:
    def __init__(self, chromsizes: Iterable[Tuple[str, int]]) -> None:
        offsets = itertools.accumulate(map(itemgetter(1), chromsizes), initial=0)
        self._offsets = OrderedDict(
            (name, (size, offset)) for (name, size), offset in zip(chromsizes, offsets)
        )

    def __call__(self, region: GenomicRegion) -> ViewInterval:
        chrom, start, end = region
        _, offset = self._offsets[chrom]
        return offset + start, offset + end

    def invert(self, interval: ViewInterval) -> List[GenomicRegion]:
        start, end = interval
        regions: List[GenomicRegion] = []
        for chrom, (size, offset) in self._offsets.items():
            if overlap((start, end), (offset, offset + size)):
                region = (
                    chrom,
                    max(offset, start) - offset,
                    min(offset + size, end) - offset,
                )
                regions.append(region)
        return regions
