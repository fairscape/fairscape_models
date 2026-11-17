""" Process Finished ROCrates to normalize inputs and outputs for evidence graph visualization

- Add Inverses
"""

from __future__ import annotations
from fairscape_models.rocrate import ROCrateV1_2
from typing import Dict, List, Optional, Tuple
from logging import Logger

EVI_NAMESPACE = "https://w3id.org/EVI#"

#: Every `owl:inverseOf` pair in the EVI ontology, as the bare JSON keys the
#: FAIRSCAPE context maps them to. Order within a pair is alphabetical; the
#: rule is symmetric so it does not matter which side is declared.
INVERSE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("associateFor", "associatedWith"),
    ("challengedBy", "challenges"),
    ("containedBy", "contains"),
    ("created", "createdBy"),
    ("datasetUsedBy", "usedDataset"),
    ("derivedFrom", "derivedTo"),
    ("describedBy", "describes"),
    ("directlyChallengedBy", "directlyChallenges"),
    ("directlySupportedBy", "directlySupports"),
    ("distributedFrom", "hasDistribution"),
    ("generated", "generatedBy"),
    ("indirectlyChallengedBy", "indirectlyChallenges"),
    ("packagedBy", "packages"),
    ("representedBy", "represents"),
    ("serviceUsedBy", "usedService"),
    ("softwareUsedBy", "usedSoftware"),
    ("supportedBy", "supports"),
    ("used", "usedBy"),
)

#: `{property: its inverse}` in both directions.
INVERSE_OF: Dict[str, str] = {}
for _a, _b in INVERSE_PAIRS:
    INVERSE_OF[_a] = _b
    INVERSE_OF[_b] = _a


class CrateProcessing:
    def __init__(self,
        self,
        crates: List[ROCrateV1_2],
        logger: Optional[Logger]
    ):
        self.crates = crates
        self.logger = logger


class GenerateInputsOutput(CrateProcessing):
    def process(self)->None:
        """ Set Inputs and Outputs property for Each ROCrate Metadata Elem for every input crate
        """
        pass

class GenerateInversesBetweenCrate(CrateProcessing):
    def process(self)->None:
        """ Adding Inverses Between ROCrates
        """
        pass


class GenerateInversesWithinCrate(CrateProcessing): 
    def process(self)->None:
        """ Within every Crate make sure inverse properties are set across crates
        """
        pass 


class GenerateIO(CrateProcessing):
    def process_all(self) -> None:
        generate_instance = GenerateInputsOutput(self.crates, self.logger)
        generate_instance.process()

        generate_inverses_within = GenerateInversesWithinCrate(self.crates, self.logger)
        generate_inverses_within.process()
        
        generate_inverses_between = GenerateInversesWithinCrate(self.crates, self.logger)
        generate_inverses_between.process()
