from urllib.request import urlretrieve

from util import find_root


def main():
    download_pad()


def download_pad():
    """Download protected areas database.
    """
    url = 'https://www.sciencebase.gov/catalog/file/get/5b030c7ae4b0da30c1c1d6de?f=__disk__76%2F3d%2F41%2F763d413a39eae08267dc583052db1214b93941e7'
    root = find_root()
    (root / 'data').mkdir(parents=True, exist_ok=True)
    urlretrieve(url, root / 'data' / 'pad.zip')


if __name__ == '__main__':
    main()
