from __future__ import annotations
from fairscape_models.rocrate import ROCrateV1_2
from typing import Optional, List
from fairscape_models.datasheet.models import *
import os
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(HERE, "templates")
DATASHEET_TEMPLATE_NAME = "datasheet.html.j2"

@lru_cache(maxsize=1)
def _environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(default_for_string=True, default=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=False,
    )
    return env

class GenerateDatasheet:
    def __init__(
        self,
        inputCrate: ROCrateV1_2,
        subcrates: Optional[List[ROCrateV1_2]]
    ):
        self.rootCrate = inputCrate
        self.subcrates = subcrates
        self.env = _environment()

    def format(self)->DatasheetPage:
        """ Use the rocrate metadata to generate the DatasheetPage object 
        """
        pass

    def generate(
        self,
        outputPath: Optional[str]
        )-> str:
        """ Generate the datasheet output for the ROCrate
        """
        datasheet_instance = self.format()
        datasheet_template = self.env.get_template(DATASHEET_TEMPLATE_NAME)

        #with open(outputPath, "w") as datasheetFile:
        context = datasheet_instance.model_dump()
        return datasheet_template.render(**context)

