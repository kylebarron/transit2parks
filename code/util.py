from pathlib import Path


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
