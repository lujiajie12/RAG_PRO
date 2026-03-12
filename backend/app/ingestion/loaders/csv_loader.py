from __future__ import annotations

from io import BytesIO

import pandas as pd

from .base_loader import BaseLoader
from ..types import ParsedDocument


class CsvLoader(BaseLoader):
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        dataframe = self._read_dataframe(data)
        if dataframe.empty:
            return ParsedDocument(
                file_name=file_name,
                file_type="csv",
                parser_name="csv",
                segments=[],
                metadata={"row_count": 0, "columns": []},
            )

        segments = []
        for row_index, row in dataframe.iterrows():
            values = []
            for column in dataframe.columns:
                value = str(row[column]).strip()
                if value:
                    values.append(f"{column}: {value}")
            if values:
                segments.append(self.make_segment("table_row", " | ".join(values), row_number=row_index + 1))
        return ParsedDocument(
            file_name=file_name,
            file_type="csv",
            parser_name="csv",
            segments=segments,
            metadata={"row_count": len(dataframe.index), "columns": list(dataframe.columns)},
        )

    @staticmethod
    def _read_dataframe(data: bytes) -> pd.DataFrame:
        options = {"dtype": str, "keep_default_na": False}
        try:
            return pd.read_csv(BytesIO(data), **options)
        except Exception:
            return pd.read_csv(BytesIO(data), sep=None, engine="python", **options)
