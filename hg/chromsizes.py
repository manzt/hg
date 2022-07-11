from __future__ import annotations

from typing import Iterable, List, Tuple, overload, Union as U
import itertools
from collections import OrderedDict

ViewInterval = Tuple[int, int]
GenomicRegion = Tuple[str, int, int]


def overlap(a: ViewInterval, b: ViewInterval) -> bool:
    return a[1] >= b[0] and a[0] <= b[1]


class Chromsizes(OrderedDict[str, int]):

    def offsets(self) -> Iterable[int]:
        return itertools.islice(
            itertools.accumulate(self.values(), initial=0),
            len(self),
        )

    def _compute_regions(self, interval: ViewInterval) -> list[GenomicRegion]:
        regions: List[GenomicRegion] = []
        for (chrom, size), offset in zip(self.items(), self.offsets()):
            if overlap(interval, (offset, offset + size)):
                region = (
                    chrom,
                    max(offset, interval[0]) - offset,
                    min(offset + size, interval[1]) - offset,
                )
                regions.append(region)
        return regions

    def _compute_interval(self, region: GenomicRegion) -> ViewInterval:
        chrom, start, end = region
        offset = dict(zip(self, self.offsets()))[chrom]
        return start + offset, end + offset

    @overload
    def convert(self, _from: GenomicRegion) -> ViewInterval:
        ...

    @overload
    def convert(self, _from: ViewInterval) -> list[GenomicRegion]:
        ...

    def convert(
        self, _from: U[ViewInterval, GenomicRegion]
    ) -> U[ViewInterval, List[GenomicRegion]]:
        if len(_from) == 2:
            return self._compute_regions(_from)
        return self._compute_interval(_from)
