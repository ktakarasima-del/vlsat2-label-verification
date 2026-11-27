"""Verify the three VLSAT-2 certificates using original DIMACS inputs."""

import argparse
import bz2
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.request import urlopen


CASE_NAMES = (
    "vlsat2_67996_13708722",
    "vlsat2_68760_13862744",
    "vlsat2_69524_14016766",
)
MANIFEST = "MANIFEST.json"
TABLE = "VLSAT2_RESULTS_100.csv"
SUMS = "SHA256SUMS.txt"
CHECKED = {
    MANIFEST, TABLE, "REPORT.pdf", "README.md", "README.ja.md", "LICENSE",
    "THIRD_PARTY_NOTICES.md", "verify_certificates.py",
    *(f"{case}.pbp.gz" for case in CASE_NAMES),
}
SOURCE_BASE = "https://cadp.inria.fr/ftp/benchmarks/vlsat/"
CHUNK = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def measure(stream, limit=None, destination=None):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(CHUNK), b""):
        size += len(block)
        require(limit is None or size <= limit, "File exceeds its expected byte size")
        digest.update(block)
        if destination is not None:
            destination.write(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def file_identity(path):
    with path.open("rb") as source:
        return measure(source)


def check_identity(actual, expected, label):
    require(actual == expected, f"{label}: byte size or SHA-256 mismatch")


def validate_table(path):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == [
            "benchmark", "variables", "clauses", "published_label",
            "verified_result", "published_label_agrees", "bundled_certificate",
        ], "Unexpected results table columns")
        rows = list(reader)
    names = set()
    changed = set()
    for row in rows:
        name = row["benchmark"]
        dims = re.fullmatch(r"vlsat2_(\d+)_(\d+)", name)
        require(dims is not None and dims.groups() == (row["variables"], row["clauses"])
                and name not in names, "Invalid or duplicate benchmark row")
        names.add(name)
        published, result = row["published_label"], row["verified_result"]
        require(published in {"SAT", "UNSAT"} and result in {"SAT", "UNSAT"},
                "Invalid verdict")
        agrees = published == result
        require(row["published_label_agrees"] == ("true" if agrees else "false"),
                "Incorrect agreement flag")
        require(row["bundled_certificate"] == (f"{name}.pbp.gz" if not agrees else ""),
                "Incorrect certificate link")
        if not agrees:
            require((published, result) == ("SAT", "UNSAT"), "Unexpected label change")
            changed.add(name)
    require(len(names) == 100 and changed == set(CASE_NAMES), "Wrong population or discrepancies")
    require(Counter(r["published_label"] for r in rows) == {"SAT": 50, "UNSAT": 50}
            and Counter(r["verified_result"] for r in rows) == {"SAT": 47, "UNSAT": 53},
            "Wrong verdict totals")


def check_package(root):
    checksums = {}
    for line in (root / SUMS).read_text(encoding="ascii").splitlines():
        digest, sep, filename = line.partition("  ")
        require(sep and SHA256.fullmatch(digest) is not None
                and filename in CHECKED and filename not in checksums,
                "Invalid checksum manifest line")
        checksums[filename] = digest
    require(checksums.keys() == CHECKED, "Missing package checksum entries")
    identities = {}
    for filename, digest in checksums.items():
        path = root / filename
        require(path.is_file() and not path.is_symlink(), f"Missing regular file: {filename}")
        identities[filename] = file_identity(path)
        require(identities[filename]["sha256"] == digest, f"{filename}: SHA-256 mismatch")
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    require(manifest["schema"] == "vlsat2-label-verification-1" and
            tuple(record["benchmark"] for record in manifest["certificates"]) == CASE_NAMES,
            "Unexpected certificate manifest")
    validate_table(root / TABLE)
    for record in manifest["certificates"]:
        name = record["benchmark"]
        proof_name = f"{name}.pbp.gz"
        require(record["proof_file"] == proof_name
                and record["source_url"] == SOURCE_BASE + f"{name}.cnf.bz2",
                "Unexpected proof filename or official input URL")
        check_identity(identities[proof_name], record["proof_gzip"], proof_name)
        with gzip.open(root / proof_name, "rb") as source:
            raw = measure(source, record["proof_pbp"]["bytes"])
        check_identity(raw, record["proof_pbp"], name + " decompressed proof")
    return manifest["certificates"]


def stage_original(record, originals, work):
    name = record["benchmark"]
    if originals is None:
        compressed = work / f"{name}.cnf.bz2"
        with urlopen(record["source_url"], timeout=60) as source, compressed.open("wb") as out:
            receipt = measure(source, record["cnf_bz2"]["bytes"], out)
        check_identity(receipt, record["cnf_bz2"], name + " download")
    else:
        compressed = originals / f"{name}.cnf.bz2"
        if compressed.is_file():
            check_identity(file_identity(compressed), record["cnf_bz2"], name + " bzip2")

    target = work / "original.cnf"
    if compressed.is_file():
        source = bz2.open(compressed, "rb")
    else:
        source = (originals / f"{name}.cnf").open("rb")
    with source, target.open("wb") as destination:
        actual = measure(source, record["cnf"]["bytes"], destination)
    check_identity(actual, record["cnf"], name + " original CNF")
    return target


def wsl_path(path):
    out = subprocess.run(["wsl.exe", "--exec", "wslpath", "-a", "-u", str(path.resolve())],
                         capture_output=True, text=True, check=True, timeout=20)
    translated = out.stdout.strip()
    require(translated.startswith("/"), "Could not translate the checker path for WSL")
    return translated


def verify_checker(command, checker, marker, timeout, env=None):
    start = monotonic()
    result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace",
                            timeout=timeout, env=env)
    require(result.returncode == 0 and marker in result.stdout.splitlines(),
            f"{checker} did not accept the proof (exit {result.returncode}). "
            + (result.stderr or result.stdout).strip()[-500:])
    return {"status": "VERIFIED_UNSAT", "exit_code": 0, "marker": marker,
            "wall_seconds": round(monotonic() - start, 3)}


def replay(record, options):
    with TemporaryDirectory(prefix="vlsat2-verify-") as temporary:
        work = Path(temporary)
        cnf = stage_original(record, options.original_dir, work)
        proof = work / "certificate.pbp"
        with gzip.open(options.bundle / record["proof_file"], "rb") as source, proof.open("wb") as out:
            actual = measure(source, record["proof_pbp"]["bytes"], out)
        check_identity(actual, record["proof_pbp"], record["benchmark"] + " proof")
        results = {
            "benchmark": record["benchmark"],
            "cnf_sha256": record["cnf"]["sha256"],
            "proof_sha256": actual["sha256"],
        }
        if options.checker in {"both", "veripb"}:
            results["VeriPB"] = verify_checker(
                [options.veripb, "--cnf", "--force-checked-deletion", str(cnf), str(proof)],
                "VeriPB", "s VERIFIED UNSATISFIABLE", options.timeout,
            )
        if options.checker in {"both", "cakepb"}:
            settings = {"CML_HEAP_SIZE": "7296", "CML_STACK_SIZE": "768"}
            cmd = [options.cakepb, str(cnf), str(proof)]
            if options.cakepb_wsl:
                cmd = ["wsl.exe", "--exec", "env",
                       *(f"{key}={val}" for key, val in settings.items()),
                       options.cakepb, wsl_path(cnf), wsl_path(proof)]
            results["CakePB"] = verify_checker(
                cmd, "CakePB", "s VERIFIED UNSAT", options.timeout,
                env=dict(os.environ, **settings),
            )
        check_identity(file_identity(cnf), record["cnf"], record["benchmark"] + " replayed CNF")
        check_identity(file_identity(proof), actual, record["benchmark"] + " replayed proof")
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--checksums-only", action="store_true")
    source.add_argument("--original-dir", type=Path, help="Directory of official .cnf.bz2 or original .cnf files")
    source.add_argument("--fetch-original", action="store_true", help="Fetch the originals from the CADP distribution")
    parser.add_argument("--case", choices=CASE_NAMES, action="append", help="Limit proof replay to selected cases")
    parser.add_argument("--checker", choices=("both", "veripb", "cakepb"), default="both")
    parser.add_argument("--veripb", default="veripb")
    parser.add_argument("--cakepb", default="cake_pb_cnf")
    parser.add_argument("--cakepb-wsl", action="store_true", help="Run CakePB in WSL from Windows")
    parser.add_argument("--timeout", type=int, default=900, help="Seconds per checker")
    options = parser.parse_args()
    if options.timeout <= 0 or (options.cakepb_wsl and os.name != "nt"):
        parser.error("Use a positive timeout. The WSL flag is available on Windows.")
    try:
        records = check_package(options.bundle)
        result = {"checksums_passed": len(CHECKED), "all_rows": 100,
                  "published_label_agreements": 97, "certificates": len(records)}
        if not options.checksums_only:
            result["replay"] = [replay(rec, options) for rec in records
                                if not options.case or rec["benchmark"] in options.case]
    except (OSError, EOFError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
