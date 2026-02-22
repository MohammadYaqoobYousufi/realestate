#!/usr/bin/env python3
"""Generate a git-filter-repo removal plan from repo metadata.

Rules:
- Always EXCLUDE src/ and backend/ and .github from removals.
- Scan git objects (via git rev-list ... | git cat-file --batch-check) or all_objects.txt if present.
- Mark any tracked paths whose single-commit blob size > 5 MB (configurable) and *not* under exclude paths.
- Also include common heavy directories: envs/, frontend/.cache/, frontend/node_modules/, ml/data/*, node_modules/ if present.
- Output:
  - filter-repo-plan.json with keys {"remove":[ "path1", "path2", ... ]}
  - filter-repo-remove-paths.txt (one path or path glob per line) for direct use with git-filter-repo --paths-from-file + --invert-paths
  - lfs_candidates.txt (file patterns recommended for Git LFS)
"""
import os, sys, json, subprocess, shlex, math
REPO_ROOT = os.path.abspath(os.getcwd())
MIN_BYTES = int(os.environ.get("MIN_REMOVE_BYTES", 5 * 1024 * 1024))  # 5MB default
EXCLUDE_PREFIXES = ("src/", "backend/", ".github/", ".git/")

def read_all_objects_file(path):
    if not os.path.exists(path):
        return []
    lines = open(path, "r", encoding="utf8", errors="ignore").read().splitlines()
    return lines

def ensure_all_objects():
    path = os.path.join(REPO_ROOT, "all_objects.txt")
    if os.path.exists(path):
        return path
    # generate it
    cmd = "git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' > all_objects.txt"
    subprocess.check_call(cmd, shell=True)
    return path

def parse_all_objects(lines):
    objs = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split(" ", 3)
        if len(parts) < 3:
            continue
        typ, sha, size = parts[0], parts[1], parts[2]
        path = parts[3].strip() if len(parts) >= 4 else ""
        try:
            sizei = int(size)
        except:
            continue
        objs.append({"type": typ, "sha": sha, "size": sizei, "path": path})
    return objs

def main():
    all_objects = ensure_all_objects()
    lines = read_all_objects_file(all_objects)
    objs = parse_all_objects(lines)
    # Candidate paths to remove
    remove_set = set()
    # Add configured heavy directories (if present)
    for d in ("envs/", "frontend/.cache/", "frontend/node_modules/", "node_modules/", "ml/artifacts/", "ml/data/"):
        if os.path.exists(os.path.join(REPO_ROOT, d.strip("/"))):
            remove_set.add(d.rstrip("/"))
    # Walk parsed objects
    for o in objs:
        p = o["path"]
        if not p:
            continue
        # skip excluded prefixes
        if any(p.startswith(pref) for pref in EXCLUDE_PREFIXES):
            continue
        if o["size"] >= MIN_BYTES:
            remove_set.add(p)
    # Filter out empty or suspicious entries
    remove_list = sorted([p for p in remove_set if p and not p.startswith(".git")])
    # write outputs
    plan = {"remove": remove_list}
    with open("filter-repo-plan.json","w",encoding="utf8") as f:
        json.dump(plan, f, indent=2)
    with open("filter-repo-remove-paths.txt","w",encoding="utf8") as f:
        for p in remove_list:
            f.write(p + "\n")
    # propose LFS patterns
    lfs_patterns = ["*.h5","*.pt","*.pkl","*.dll","*.so","*.bin","*.onnx","*.parquet","*.tar.gz","*.zip","*.mp4","*.wav"]
    with open("lfs_candidates.txt","w",encoding="utf8") as f:
        for pattern in lfs_patterns:
            f.write(pattern + "\n")
    print(f"Wrote filter-repo-plan.json with {len(remove_list)} paths. See filter-repo-remove-paths.txt and lfs_candidates.txt")
if __name__ == '__main__':
    main()
