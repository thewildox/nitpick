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

patch = """@@ -10,6 +10,8 @@ def process_data(items):
     results = []
     for item in items:
-        results.append(transform(item))
+        if item is not None:
+            results.append(transform(item))
     total = len(results)
     return results"""

print(changed_lines(patch))