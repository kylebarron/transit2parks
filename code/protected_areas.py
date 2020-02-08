from keplergl_quickvis import Visualize as Vis
import fiona
import geopandas as gpd
from util import find_root
from zipfile import ZipFile
from constants import DESIGNATION_TYPES

PAD_PROJECTION = (
    f"""\
PROJCS["USA_Contiguous_Albers_Equal_Area_Conic_USGS_version",
    GEOGCS["NAD83",
        DATUM["North_American_Datum_1983",
            SPHEROID["GRS 1980",6378137,298.257222101,
                AUTHORITY["EPSG","7019"]],
            AUTHORITY["EPSG","6269"]],
        PRIMEM["Greenwich",0],
        UNIT["Degree",0.0174532925199433]],
    PROJECTION["Albers_Conic_Equal_Area"],
    PARAMETER["latitude_of_center",23],
    PARAMETER["longitude_of_center",-96],
    PARAMETER["standard_parallel_1",29.5],
    PARAMETER["standard_parallel_2",45.5],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["Esri","102039"]]
""")
# https://www.sciencebase.gov/catalog/file/get/5cc0e84be4b09b8c0b72927a?f=__disk__5a%2F81%2F75%2F5a8175a324b2e069554eaa00afa2d573c1eecb13
# https://www.sciencebase.gov/catalog/file/get/5cc0e84be4b09b8c0b72927a?f=__disk__27%2F91%2Fe8%2F2791e8316bac5f72a31d1a6722f212f3b7239fc2

from pyproj import CRS
proj = CRS(PAD_PROJECTION)


def main():
    root = find_root()
    data_dir = root / 'data'


def get_public_areas_in_state():
    root = find_root()
    data_dir = root / 'data'
    zip_path = data_dir / 'PADUS2_0CO_Arc10GDB.zip'

    gdb_files = find_gdb_in_zip(zip_path)
    assert len(gdb_files) == 1, '>1 gdb file in zip'
    gdb_file = gdb_files[0]
    path = f'zip://{str(zip_path)}!{gdb_file}'

    combined_layer = find_combined_layer(path)

    gdf = gpd.read_file(path, layer=combined_layer)
    # Add projection manually
    gdf.crs = proj
    # Reproject to EPSG 4326
    gdf = gdf.to_crs(epsg=4326)

    # Filter by designation type
    allowed_desig_types = DESIGNATION_TYPES.keys()
    gdf = gdf[gdf['Des_Tp'].isin(allowed_desig_types)]

    # Filter by allowed Access
    # RESTRICTED_ACCESS ('RA') is included because this refers to stuff like
    # permits. So for example Rocky Mountain National Park Wilderness is
    # included in RESTRICTED_ACCESS because you need a permit for some
    # recreational uses.
    OPEN_ACCESS = 'OA'
    RESTRICTED_ACCESS = 'RA'
    allowed_access = [OPEN_ACCESS, RESTRICTED_ACCESS]
    gdf = gdf[gdf['Access'].isin(allowed_access)]


def find_gdb_in_zip(zip_path):
    with ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Find gdb file(s) (it's actually a folder, hence /)
        return [x for x in names if x.endswith('.gdb/')]


def find_combined_layer(path):
    """Find name of layer with combined categories

    Args:
        - path: path to file. If the path is a zipfile, must be of format:

            ```
            zip:///path/to/zip/file.zip!gdb_file.gdb
            ```
    """
    layers = fiona.listlayers(path)

    match = 'Fee_Designation_Easement'
    matched_layers = [x for x in layers if match in x]
    assert len(matched_layers) == 1, '>1 matched layer'
    return matched_layers[0]
