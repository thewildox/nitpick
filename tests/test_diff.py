from app.analysis.diff import changed_lines


def test_changed_lines_basic():
    patch = """@@ -10,6 +10,8 @@ def process_data(items):
     results = []
     for item in items:
-        results.append(transform(item))
+        if item is not None:
+            results.append(transform(item))
     total = len(results)
     return results"""
    assert changed_lines(patch) == {12, 13}


def test_changed_lines_deletions_only():
    patch = """@@ -10,4 +10,2 @@ def process_data(items):
     results = []
     for item in items:
-        results.append(transform(item))
-        return results"""
    assert changed_lines(patch) == set()


def test_changed_lines_multiple_hunks():
    patch = """@@ -10,3 +10,4 @@ def process_data(items):
     results = []
+    results.clear()
     for item in items:
         pass
@@ -30,2 +31,3 @@ def summarize(results):
     total = len(results)
+    print(total)
     return total"""
    assert changed_lines(patch) == {11, 32}