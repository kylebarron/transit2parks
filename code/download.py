from pathlib import Path
from urllib.request import urlretrieve


def main():
    download_pad()


def download_pad():
    """Download protected areas database.
    """
    url = 'https://www.sciencebase.gov/catalog/file/get/5b030c7ae4b0da30c1c1d6de?f=__disk__76%2F3d%2F41%2F763d413a39eae08267dc583052db1214b93941e7'
    root = find_root()
    (root / 'data').mkdir(parents=True, exist_ok=True)
    urlretrieve(url, root / 'data' / 'pad.zip')


def find_root():
    cwd = Path('.').resolve()

    i = -1
    while True:
        search_path = cwd if i < 0 else cwd.parents[i]

        # Search for `.root`
        rootfile = [x for x in search_path.iterdir() if x.name == '.root']
        if rootfile:
            return search_path

        i += 1

if __name__ == '__main__':
    main()
