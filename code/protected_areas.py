from urllib.request import urlretrieve
from zipfile import ZipFile

import fiona
import geopandas as gpd
import requests
from bs4 import BeautifulSoup
from keplergl_quickvis import Visualize as Vis
from pyproj import CRS

from constants import DESIGNATION_TYPES
from util import find_root

PAD_PROJECTION = CRS(
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

# TODO: use http://epsg.io/102003 for buffer


def main():
    root = find_root()
    download_dir = root / 'data' / 'raw_gdb'
    download_dir.mkdir(exist_ok=True, parents=True)
    state_download_urls = get_urls()

    # state_name = 'district_of_columbia'
    # download_url = state_download_urls[state_name]
    for state_name, download_url in state_download_urls.items():
        # Download GDB file
        local_path = download_dir / (state_name + '.gdb.zip')
        if not local_path.exists():
            # TODO: update to use tqdm
            urlretrieve(download_url, local_path)


# gdb_zip_path = data_dir / 'PADUS2_0CO_Arc10GDB.zip'
def get_public_areas_in_state(gdb_zip_path):

    gdb_files = find_gdb_in_zip(gdb_zip_path)
    assert len(gdb_files) == 1, f'>1 gdb file in zip: {gdb_files}'
    gdb_file = gdb_files[0]
    path = f'zip://{str(gdb_zip_path)}!{gdb_file}'

    combined_layer = find_combined_layer(path)

    gdf = gpd.read_file(path, layer=combined_layer)
    # Add projection manually
    gdf.crs = PAD_PROJECTION
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

    return gdf


def find_gdb_in_zip(zip_path):
    """Find Geodatabase name(s) in Zip file

    Args:
        - zip_path: path to Zip file

    Returns:
        str: name(s)
    """
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

    Returns:
        str: name of combined layer in Geodatabase file
    """
    layers = fiona.listlayers(path)

    match = 'Fee_Designation_Easement'
    matched_layers = [x for x in layers if match in x]
    assert len(matched_layers) == 1, '!=1 matched layer'
    return matched_layers[0]


def get_urls():
    """Get PAD download urls by state

    Returns:
        dict: key is name of state with _ between words, lower case. value is download url
    """
    url = 'https://www.usgs.gov/core-science-systems/science-analytics-and-synthesis/gap/science/pad-us-data-download'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    p = soup.find('p', text='Download PAD-US by State / Territory')
    state_list_ul = p.find_next('ul')

    state_links = state_list_ul.find_all('li')
    gdb_links = []
    for state_link in state_links:
        gdb_link = [
            a for a in state_link.find_all('a') if 'Geodatabase' in a.text][0]
        gdb_links.append(gdb_link)

    drop_states = [
        'American Samoa', 'Alaska', 'Hawaii', 'Northern Mariana', 'Guam',
        'Puerto Rico', 'Virgin Islands']

    state_links_filtered = [
        x for x in gdb_links if not any(
            drop_state.lower() in x.text.lower() for drop_state in drop_states)]
    urls = {}
    for state_link in state_links_filtered:
        text = state_link.text.lower()
        state_name = text.replace('geodatabase', '').strip().replace(' ', '_')
        url = state_link.attrs['href']
        urls[state_name] = url

    return urls
