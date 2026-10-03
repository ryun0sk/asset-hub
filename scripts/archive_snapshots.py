"""Freeze archived research snapshots so they can always be verified and restored.

Each target lives in research/{themes,companies}/<slug>/<YYYY-MM-DD>/. The newest dated folder
of a target is its current version; every older folder is an archive and must not change.
research/archive-manifest.json records the size and SHA-256 of every file in each archive
(working/, qa/ and hidden files are local-only and excluded, as in .gitignore).

    python3 scripts/archive_snapshots.py            # same as --check
    python3 scripts/archive_snapshots.py --check    # exit 1 when an archive is unrecorded or changed
    python3 scripts/archive_snapshots.py --write    # record archives that are not in the manifest yet
    python3 scripts/archive_snapshots.py --restore  # put changed or missing archive files back from git history

--write never rewrites an archive that is already recorded: fix the files (or --restore them)
instead. --restore searches every commit for a blob with the recorded hash, so it works as long
as the snapshot was committed once.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
MANIFEST = RESEARCH / "archive-manifest.json"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOCAL_ONLY = {"working", "qa"}


def archived_folders():
    """Every dated folder except the newest one of its target, as repo-relative paths.

    Folders holding only local files (working/, qa/) are not versions yet, matching
    build_catalog.py, so a research run in progress does not turn the current version into
    an archive.
    """
    folders = []
    for group in ("themes", "companies"):
        base = RESEARCH / group
        for target in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
            dated = sorted(p for p in target.iterdir() if p.is_dir() and DATE.match(p.name))
            dated = [p for p in dated if snapshot_files(p.relative_to(ROOT).as_posix())]
            folders.extend(p.relative_to(ROOT).as_posix() for p in dated[:-1])
    return folders


def snapshot_files(folder):
    root = ROOT / folder
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in LOCAL_ONLY or part.startswith(".") for part in relative.parts):
            continue
        files.append(relative.as_posix())
    return files


def digest(data):
    return hashlib.sha256(data).hexdigest()


def record(folder):
    return {name: {"bytes": (ROOT / folder / name).stat().st_size, "sha256": digest((ROOT / folder / name).read_bytes())} for name in snapshot_files(folder)}


def load():
    if not MANIFEST.exists():
        return {"version": 1, "archives": {}}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def problems(manifest):
    """List of (folder, file or None, message) for everything that does not match the manifest."""
    found = []
    recorded = manifest.get("archives", {})
    for folder in archived_folders():
        if folder not in recorded:
            found.append((folder, None, "archive is not recorded; run --write"))
    for folder, files in recorded.items():
        if not (ROOT / folder).is_dir():
            found.append((folder, None, "archive folder is missing"))
        present = set(snapshot_files(folder)) if (ROOT / folder).is_dir() else set()
        for name, expected in files.items():
            path = ROOT / folder / name
            if name not in present:
                found.append((folder, name, "missing"))
            elif digest(path.read_bytes()) != expected["sha256"]:
                found.append((folder, name, "changed"))
        for name in sorted(present - set(files)):
            found.append((folder, name, "added after the archive was recorded"))
    return found


def git(*args, binary=False):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode()


def restore(manifest):
    """Rewrite changed or missing files from the newest commit whose blob has the recorded hash.

    Returns what still differs afterwards (unrecorded archives, added files, lost content).
    """
    for folder, name, message in problems(manifest):
        if name is None or message not in ("missing", "changed"):
            continue
        path = f"{folder}/{name}"
        expected = manifest["archives"][folder][name]["sha256"]
        for commit in git("rev-list", "--all", "--", path).split():
            try:
                data = git("show", f"{commit}:{path}", binary=True)
            except subprocess.CalledProcessError:
                continue
            if digest(data) == expected:
                (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
                (ROOT / path).write_bytes(data)
                print(f"restored {path} from {commit[:12]}")
                break
        else:
            print(f"{path}: no commit has the recorded content")
    return problems(manifest)


def report(found):
    for folder, name, message in found:
        print(f"{folder}/{name}: {message}" if name else f"{folder}: {message}")


def main(argv):
    manifest = load()
    if "--write" in argv:
        added = [folder for folder in archived_folders() if folder not in manifest["archives"]]
        for folder in added:
            manifest["archives"][folder] = record(folder)
        manifest["archives"] = dict(sorted(manifest["archives"].items()))
        if added:
            MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"recorded {len(added)} archive(s): {', '.join(added)}" if added else "no new archives")
        found = problems(manifest)
        if found:
            report(found)
            raise SystemExit(1)
        return
    if "--restore" in argv:
        found = restore(manifest)
        if found:
            report(found)
            raise SystemExit(1)
        print("all archives match research/archive-manifest.json")
        return
    found = problems(manifest)
    if found:
        report(found)
        raise SystemExit("archived snapshots differ from research/archive-manifest.json (see above; --restore puts files back)")
    print(f"{len(manifest['archives'])} archive(s) match research/archive-manifest.json")


if __name__ == "__main__":
    main(sys.argv[1:])
