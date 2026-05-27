import csv
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, model_validator
from typing import Optional, List, Union, Tuple
from enum import Enum

from fairscape_models.fairscape_base import IdentifierValue, DATASET_TYPE
from fairscape_models.digital_object import DigitalObject


TABULAR_FORMATS = {"csv", "tsv", "text/csv", "text/tab-separated-values"}
TABULAR_EXTENSIONS = {".csv", ".tsv"}


def _count_csv(path: Path, delimiter: str) -> Tuple[int, int]:
    """Stream a csv/tsv counting data rows and columns (header excluded from rowCount)."""
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return 0, 0
        cols = len(header)
        rows = sum(1 for _ in reader)
    return rows, cols


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024


class SplitType(str, Enum):
    """Croissant-aligned split type semantics.

    Maps to:
      cr:TrainingSplit   -> "train"
      cr:ValidationSplit -> "validation"
      cr:TestSplit       -> "test"
      custom             -> "other"
    """
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    OTHER = "other"


class Split(BaseModel):
    """A named partition or subset of a Dataset.

    Unifies concepts from D4D DataSubset/SamplingStrategy and Croissant cr:Split.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Identity 
    name: str
    description: Optional[str] = Field(default=None)

    # Croissant split semantics (maps to cr:TrainingSplit, etc.)
    splitType: Optional[SplitType] = Field(default=None)

    # Query information SQL or croissant extract transform
    query: Optional[str] = Field(default=None)
    queryType: Optional[str] = Field(default=None)

    sourceDatasets: Optional[List[IdentifierValue]] = Field(default=None)

    # D4D sampling strategy (flat, all optional)
    isSample: Optional[bool] = Field(default=None)
    isRandom: Optional[bool] = Field(default=None)
    samplingStrategy: Optional[str] = Field(default=None)

class Dataset(DigitalObject):
    metadataType: Optional[Union[List[str], str]] = Field(default=['prov:Entity', "https://w3id.org/EVI#Dataset"], alias="@type")
    additionalType: Optional[str] = Field(default=DATASET_TYPE)
    datePublished: str = Field(...)
    keywords: List[str] = Field(...)
    fileFormat: str = Field(alias="format")
    dataSchema: Optional[IdentifierValue] = Field(
        validation_alias=AliasChoices('evi:Schema', 'EVI:Schema', 'schema', 'evi:schema'),
        serialization_alias='evi:Schema',
        default=None
    )
    generatedBy: Optional[Union[IdentifierValue, List[IdentifierValue]]] = Field(default=[])
    derivedFrom: Optional[List[IdentifierValue]] = Field(default=[])
    splits: Optional[List[Split]] = Field(default=None)

    # statistics support AI-Ready rubric 2.b Statistics).
    contentSize: Optional[str] = Field(default=None, description="Total size of the dataset content (e.g. '2.4 GB', '150 MB').")
    rowCount: Optional[int] = Field(default=None, description="Number of rows / records for tabular datasets.")
    columnCount: Optional[int] = Field(default=None, description="Number of columns / fields for tabular datasets.")
    sampleSize: Optional[int] = Field(default=None, description="Number of samples represented by the dataset (often == rowCount for tabular data, but may differ).")
    hasSummaryStatistics: Optional[Union[str, IdentifierValue]] = Field(default=None, description="Reference to a summary statistics entity describing distributions, counts, and key statistics for this dataset.")

    def add_summary_stats(
        self,
        file_path: Optional[Union[str, Path]] = None,
        crate_root: Optional[Union[str, Path]] = None,
    ) -> "Dataset":
        """Compute row/column counts for a tabular Dataset and produce a linked stats child.

        Reads ``self.contentUrl`` (or an explicit ``file_path`` override) as csv/tsv
        using the stdlib ``csv`` module — no pandas / no extra deps. Populates
        ``rowCount``, ``columnCount``, ``contentSize``, ``sampleSize`` on ``self``
        and on a newly-constructed child ``Dataset``. Sets ``self.hasSummaryStatistics``
        to the child's ``@id`` and returns the child so the caller can append it
        to the RO-Crate ``@graph``.

        Remote URLs and non-csv/tsv formats are out of scope here — use the
        ``fairscape augment summary-stats`` CLI command for parquet / http(s) /
        per-column statistics.
        """
        resolved = self._resolve_tabular_path(file_path, crate_root)
        delimiter = "\t" if resolved.suffix.lower() == ".tsv" or "tab" in (self.fileFormat or "").lower() else ","
        rows, cols = _count_csv(resolved, delimiter)
        size_bytes = resolved.stat().st_size
        size_str = _human_size(size_bytes)

        self.rowCount = rows
        self.columnCount = cols
        self.contentSize = size_str
        if self.sampleSize is None:
            self.sampleSize = rows

        stats_guid = f"{self.guid.rstrip('/')}/summary-stats"
        stats = Dataset(
            guid=stats_guid,
            name=f"{self.name} — Summary Statistics",
            author=self.author,
            description=f"Row and column counts for {self.name} ({self.guid}), generated from the source tabular file.",
            datePublished=self.datePublished,
            keywords=(self.keywords or []) + ["summary-statistics"],
            fileFormat="application/json",
            rowCount=rows,
            columnCount=cols,
            contentSize=size_str,
            sampleSize=rows,
            derivedFrom=[IdentifierValue(**{"@id": self.guid})],
        )
        self.hasSummaryStatistics = IdentifierValue(**{"@id": stats_guid})
        return stats

    def _resolve_tabular_path(
        self,
        file_path: Optional[Union[str, Path]],
        crate_root: Optional[Union[str, Path]],
    ) -> Path:
        if file_path is not None:
            p = Path(file_path)
            if not p.exists():
                raise FileNotFoundError(f"file_path does not exist: {p}")
            self._require_tabular(p)
            return p

        if not self.contentUrl:
            raise ValueError(f"Dataset {self.guid} has no contentUrl; pass file_path explicitly.")

        url = self.contentUrl if isinstance(self.contentUrl, str) else self.contentUrl[0]
        if url.startswith(("http://", "https://")):
            raise NotImplementedError(
                "Remote contentUrl is not supported by add_summary_stats; use the "
                "`fairscape augment summary-stats` CLI command, or pass file_path."
            )

        if url.startswith("file://"):
            rel = url[len("file://"):].lstrip("/")
            if crate_root is None:
                raise ValueError(
                    f"contentUrl {url!r} is crate-relative; pass crate_root to resolve."
                )
            p = Path(crate_root) / rel
        else:
            p = Path(url)
            if not p.is_absolute() and crate_root is not None:
                p = Path(crate_root) / p

        if not p.exists():
            raise FileNotFoundError(f"Resolved contentUrl does not exist: {p}")
        self._require_tabular(p)
        return p

    def _require_tabular(self, path: Path) -> None:
        fmt = (self.fileFormat or "").lower()
        ext = path.suffix.lower()
        if fmt in TABULAR_FORMATS or ext in TABULAR_EXTENSIONS:
            return
        raise ValueError(
            f"Dataset {self.guid} is not csv/tsv (fileFormat={self.fileFormat!r}, "
            f"extension={ext!r}); use the CLI augment summary-stats command for richer formats."
        )

    @model_validator(mode='after')
    def populate_prov_fields(self):
        """Auto-populate PROV-O fields from EVI fields"""
        self.metadataType = ['prov:Entity', "https://w3id.org/EVI#Dataset"]

        # Map generatedBy → prov:wasGeneratedBy
        if self.generatedBy:
            if isinstance(self.generatedBy, list):
                self.wasGeneratedBy = self.generatedBy
            else:
                self.wasGeneratedBy = [self.generatedBy]
        else:
            self.wasGeneratedBy = []

        # Map derivedFrom → prov:wasDerivedFrom
        self.wasDerivedFrom = self.derivedFrom or []

        # Map author
        if self.author:
            if isinstance(self.author, str):
                self.wasAttributedTo = [self.author]
            elif isinstance(self.author, list):
                self.wasAttributedTo = [a for a in self.author]
        else:
            self.wasAttributedTo = []

        return self