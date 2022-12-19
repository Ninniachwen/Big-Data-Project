from abc import ABC, abstractmethod
import pandas as pd
from zipfile import ZipFile
import io
from pathlib import Path
import urllib.request
from tempfile import TemporaryDirectory

from typing import Iterable, Optional, List

class Chunk(ABC):
    def __init__(self, chunk_label: any):
        self.chunk_label = chunk_label
        self.init_chunk()
    
    @abstractmethod
    def init_chunk(self) -> None:
        pass

    @abstractmethod
    def get_part_labels(self) -> Iterable[any]:
        pass

    @abstractmethod
    def get_part(self, part_label: any) -> pd.DataFrame:
        pass

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    @abstractmethod
    def get_chunk_labels(cls) -> Iterable[any]:
        pass

class GitChunk(Chunk):
    def __init__(self, chunk_label: str, cache_dir: Optional[Path]=Path(__file__).parent.parent/"data/zip_cache"):
        self.cache_dir = cache_dir
        self.temp_dir = None
        super().__init__(chunk_label)


    def init_chunk(self) -> None:
        if self.cache_dir is None:
            self.temp_dir = TemporaryDirectory()
            self.cache_dir = Path(self.temp_dir.name)
        else:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        zip_path = (self.cache_dir / self.chunk_label).with_suffix(".zip")
        if not zip_path.exists():
            urllib.request.urlretrieve(
                "https://zenodo.org/record/6517052/files/" + self.chunk_label + ".zip",
                zip_path)
        self.zf = ZipFile(zip_path)

    def get_part_labels(self) -> List[str]:
        return self.zf.namelist()

    def get_part(self, part_label: str) -> pd.DataFrame:
        if not Path(part_label).suffix != 'parquet':  # optional filtering by filetype
            return None
        try:
            table_name = str(self.chunk_label.replace("'", '') + '_' + Path(part_label).stem)
            pq_bytes = self.zf.read(part_label)
            pq_file_like = io.BytesIO(pq_bytes)
            df = pd.read_parquet(pq_file_like, engine="fastparquet")
            df.columns.name = table_name
            return df
        except Exception as e:
            print(f"Error: {part_label=}, {self.chunk_label=} ->", e)
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.zf.close()
        if self.temp_dir is not None:
            self.temp_dir.cleanup()

        

    @classmethod
    def get_chunk_labels(cls) -> List[str]:
        return [chunk_label for chunk_label in (Path(__file__).parent.parent / "data/gittable_parts.txt").read_text().split('\n') if chunk_label != '']

class DresdenChunk(Chunk):
    pass

class DuckDBChunk(Chunk):
    pass

