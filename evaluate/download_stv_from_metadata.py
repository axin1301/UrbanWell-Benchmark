import argparse
import json
import os
from pathlib import Path
from typing import Any

import streetview


DEFAULT_FOV = 90
DEFAULT_PITCH = 0
DEFAULT_IMAGE_FORMAT = "jpeg"
GOOGLE_KEY_ENV = "GOOGLE_KEY_MY"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Street View images for evaluation from metadata_stv JSON."
    )
    parser.add_argument(
        "metadata_json",
        type=Path,
        help="Path to metadata_stv JSON. The file must be a list of metadata objects.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("stv-image"),
        help="Directory used to store the final Street View images. Default: stv-image",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Google Street View API key. If omitted, the script reads GOOGLE_KEY_MY.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip entries when the target file already exists.",
    )
    return parser.parse_args()


def load_metadata(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError("metadata_stv JSON must be a list of objects.")
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise TypeError(f"metadata item {idx} is not an object.")
    return data


def require_key(item: dict[str, Any], key: str, index: int) -> Any:
    if key not in item:
        raise KeyError(f"metadata item {index} is missing `{key}`.")
    return item[key]


def validate_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    validated = {
        "image_name": str(require_key(item, "image_name", index)),
        "city_name": str(require_key(item, "city_name", index)),
        "identifier": str(require_key(item, "identifier", index)),
        "year": int(require_key(item, "year", index)),
        "date": str(require_key(item, "date", index)),
        "pano_id": str(require_key(item, "pano_id", index)),
        "heading": int(require_key(item, "heading", index)),
        "query_lat": float(require_key(item, "query_lat", index)),
        "query_lon": float(require_key(item, "query_lon", index)),
        "returned_lat": float(require_key(item, "returned_lat", index)),
        "returned_lon": float(require_key(item, "returned_lon", index)),
        "pitch": int(item.get("pitch", DEFAULT_PITCH)),
        "fov": int(item.get("fov", DEFAULT_FOV)),
        "source": str(item.get("source", "google_street_view")),
    }
    return validated


def build_output_path(output_dir: Path, item: dict[str, Any]) -> Path:
    return output_dir / item["city_name"] / item["identifier"] / "street_view_images" / item["image_name"]


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.metadata_json)

    api_key = args.api_key or os.getenv(GOOGLE_KEY_ENV, "")
    if not api_key:
        raise ValueError(
            "Google Street View API key is required. Pass --api-key or set GOOGLE_KEY_MY."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    for index, raw_item in enumerate(metadata):
        item = validate_item(raw_item, index)
        output_path = build_output_path(args.output_dir, item)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        manifest_entry = {
            "index": index,
            **item,
            "output_path": str(output_path),
        }

        if args.skip_existing and output_path.exists():
            manifest_entry["status"] = "skipped_existing"
            manifest.append(manifest_entry)
            print(f"[skip] {output_path}")
            continue

        print(
            f"[download] city={item['city_name']} identifier={item['identifier']} "
            f"year={item['year']} heading={item['heading']} pano_id={item['pano_id']}"
        )
        response = streetview.get_streetview(
            pano_id=item["pano_id"],
            heading=item["heading"],
            fov=item["fov"],
            pitch=item["pitch"],
            api_key=api_key,
        )
        response.save(str(output_path), DEFAULT_IMAGE_FORMAT)

        manifest_entry["status"] = "downloaded"
        manifest.append(manifest_entry)
        print(f"[saved] {output_path}")

    manifest_path = args.output_dir / "metadata_stv_download_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[manifest] {manifest_path}")


if __name__ == "__main__":
    main()
