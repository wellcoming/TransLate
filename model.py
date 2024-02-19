from pathlib import Path
from typing import List, Tuple, Union

import yaml
from pydantic import BaseModel, Field, validator, field_serializer
from pydantic_core.core_schema import FieldSerializationInfo


class FDPath(BaseModel):
    path: Path
    dpath: Tuple[Union[str, int], ...]

    @field_serializer('path')
    def _(self, path: Path, info: FieldSerializationInfo):
        return str(path)

    def __str__(self):
        return f"{self.path}:{'.'.join(self.dpath)}"


class Translate(BaseModel):
    ori: str
    trans: str
    path: FDPath
