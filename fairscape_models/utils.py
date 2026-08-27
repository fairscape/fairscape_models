import zipfile
import json
import pathlib
from fairscape_models.rocrate import ROCrateV1_2


def findCrateRootMetadata(
    cratePath: pathlib.Path,
    )->bytes | None:
    """ Returns bytes json of a zipped ROCrate ro-crate-metadata.json file
    """

    with zipfile.ZipFile(str(cratePath), 'r') as zip_ref:
        namelist = zip_ref.namelist()

        if 'ro-crate-metadata.json' in namelist:
            return zip_ref.read('ro-crate-metadata.json')

        # TODO issue with subfolders, elements can be inside subfolders without folder existing in namelist
        # i.e. root/ro-crate-metadata.json can exist without root/ appearing in the namelist

        #find root subfolder
        #
        # subfolders = [ elem for elem in namelist if elem.endswith("/") and elem.count("/") == 1]
        # return namelist

        #	TODO exception for multiple root crates in 
        # if len(subfolders) != 1:
        #	raise Exception
        #crateZipPath = subfolders[0] + "ro-crate-metadata.json"
        # TODO exception
        #if crateZipPath not in namelist:
        #	raise Exception

        matchingROCrates = [ elem for elem in namelist if 'ro-crate-metadata.json' in elem]

        if len(matchingROCrates) > 1:
            raise Exception
        else:
            # read the content	
            return zip_ref.read(matchingROCrates[0])


def readCrate(
    cratePath: pathlib.Path,
    ) -> ROCrateV1_2 | None:
    """ Given a path to a zipped crate read the rocrate json into an ROCrateV1_2"""

    if cratePath.suffix == ".zip" and cratePath.is_file():
        rootCrateJSON = findCrateRootMetadata(cratePath)

    # TODO if crate is unzipped
    else:
        raise Exception("Only for Zipped Crates")

    try:
        return ROCrateV1_2.model_validate_json(rootCrateJSON)
    except Exception as e:
        return e.errors()
