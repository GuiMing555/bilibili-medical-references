from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "id",
    "title",
    "authors_or_organization",
    "year",
    "kind",
    "doi_or_standard",
    "source_url",
    "license",
    "distribution_mode",
    "local_file",
    "sha256",
    "video_usage",
}
OPEN_LICENSE_PREFIXES = ("CC BY", "CC0", "PUBLIC DOMAIN")


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        if columns != REQUIRED_COLUMNS:
            missing = sorted(REQUIRED_COLUMNS - columns)
            extra = sorted(columns - REQUIRED_COLUMNS)
            errors.append(f"{path}: columns mismatch; missing={missing}, extra={extra}")
            return errors

        rows = list(reader)

    if not rows:
        errors.append(f"{path}: no reference rows")
        return errors

    seen_ids: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        prefix = f"{path}:{line_number}"
        reference_id = row["id"].strip()
        if not reference_id or reference_id in seen_ids:
            errors.append(f"{prefix}: id is empty or duplicated")
        seen_ids.add(reference_id)

        if not row["title"].strip() or not row["authors_or_organization"].strip():
            errors.append(f"{prefix}: title and authors_or_organization are required")
        if not is_http_url(row["source_url"].strip()):
            errors.append(f"{prefix}: source_url must be an http(s) URL")

        mode = row["distribution_mode"].strip()
        local_file = row["local_file"].strip()
        declared_hash = row["sha256"].strip().lower()
        license_name = row["license"].strip().upper()

        if mode == "file":
            if not local_file:
                errors.append(f"{prefix}: file mode requires local_file")
                continue
            if not license_name.startswith(OPEN_LICENSE_PREFIXES):
                errors.append(f"{prefix}: file mode requires an explicit open licence")
            document = path.parent / local_file
            if not document.is_file():
                errors.append(f"{prefix}: missing file {document}")
                continue
            actual_hash = sha256(document)
            if actual_hash != declared_hash:
                errors.append(
                    f"{prefix}: sha256 mismatch for {local_file}; "
                    f"expected={declared_hash}, actual={actual_hash}"
                )
        elif mode == "link-only":
            if local_file or declared_hash:
                errors.append(f"{prefix}: link-only rows must not declare a local file/hash")
        else:
            errors.append(f"{prefix}: distribution_mode must be file or link-only")

    return errors


def main() -> int:
    manifests = sorted(ROOT.glob("*/*/[0-9][0-9]/references.csv"))
    if not manifests:
        print("No episode manifests found")
        return 1

    errors: list[str] = []
    for manifest in manifests:
        errors.extend(validate_manifest(manifest))

    if errors:
        print("Reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(manifests)} episode manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

