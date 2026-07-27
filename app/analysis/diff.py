import re


def changed_lines(patch: str) -> set[int]:
    lines = patch.splitlines()
    result = set()
    counter = 0

    for line in lines:
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            counter = int(match.group(1))
        elif line.startswith("+"):
            result.add(counter)
            counter += 1
        elif line.startswith("-"):
            pass
        else:
            counter += 1

    return result