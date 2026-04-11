import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download satellite images for evaluation from metadata_sat JSON."
    )
    parser.add_argument(
        "metadata_json",
        type=Path,
        help="Path to metadata_sat JSON. The file must be a list of metadata objects.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sat-image"),
        help="Directory used to store the final satellite images. Default: sat-image",
    )
    parser.add_argument(
        "--downloader-exe",
        type=Path,
        default=Path("downloader.exe"),
        help="Path to downloader.exe. Default: downloader.exe",
    )
    parser.add_argument(
        "--zoom-level",
        type=int,
        default=16,
        help="Zoom level passed to downloader.exe. Default: 16",
    )
    parser.add_argument(
        "--date-suffix",
        default="07-31",
        help="Month-day suffix used to build the imagery date. Default: 07-31",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip entries when the target file already exists.",
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep the raw downloader outputs under sat-image/_raw.",
    )
    return parser.parse_args()


def load_metadata(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise TypeError("metadata_sat JSON must be a list of objects.")
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise TypeError(f"metadata item {idx} is not an object.")
    return data


def validate_item(item: dict[str, Any], index: int) -> tuple[str, int, list[float], str]:
    required_keys = ["sat_image_name", "year", "boundary", "city_name"]
    for key in required_keys:
        if key not in item:
            raise KeyError(f"metadata item {index} is missing `{key}`.")

    sat_image_name = str(item["sat_image_name"])
    year = int(item["year"])
    city_name = str(item["city_name"])
    boundary = item["boundary"]

    if not isinstance(boundary, list) or len(boundary) != 4:
        raise ValueError(
            f"metadata item {index} has invalid `boundary`. Expected [min_lat, max_lat, min_lng, max_lng]."
        )

    try:
        min_lat, max_lat, min_lng, max_lng = [float(value) for value in boundary]
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"metadata item {index} contains non-numeric boundary values.") from exc

    if min_lat >= max_lat:
        raise ValueError(f"metadata item {index} has min_lat >= max_lat.")
    if min_lng >= max_lng:
        raise ValueError(f"metadata item {index} has min_lng >= max_lng.")

    return sat_image_name, year, [min_lat, max_lat, min_lng, max_lng], city_name


def build_downloader_command(
    downloader_exe: Path,
    city_name: str,
    zoom_level: int,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    raw_output_dir: Path,
    date_str: str,
) -> list[str]:
    return [
        str(downloader_exe),
        city_name,
        str(zoom_level),
        str(zoom_level),
        str(min_lng),
        str(max_lng),
        str(max_lat),
        str(min_lat),
        str(raw_output_dir),
        date_str,
    ]


def find_downloaded_image(raw_output_dir: Path, sat_image_name: str) -> Path | None:
    exact_matches = list(raw_output_dir.rglob(sat_image_name))
    if exact_matches:
        return exact_matches[0]

    image_files = [
        path
        for path in raw_output_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if len(image_files) == 1:
        return image_files[0]
    return None


def main() -> None:
    args = parse_args()
    metadata = load_metadata(args.metadata_json)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = args.output_dir / "_raw"
    manifest: list[dict[str, Any]] = []

    if not args.downloader_exe.exists():
        raise FileNotFoundError(
            f"Cannot find downloader executable: {args.downloader_exe}. "
            "Please install or place downloader.exe in the working directory, or pass --downloader-exe."
        )

    for index, item in enumerate(metadata):
        sat_image_name, year, boundary, city_name = validate_item(item, index)
        min_lat, max_lat, min_lng, max_lng = boundary
        date_str = f"{year}-{args.date_suffix}"

        final_dir = args.output_dir / str(year) / city_name
        final_dir.mkdir(parents=True, exist_ok=True)
        final_image_path = final_dir / sat_image_name

        manifest_entry: dict[str, Any] = {
            "index": index,
            "sat_image_name": sat_image_name,
            "year": year,
            "city_name": city_name,
            "boundary": boundary,
            "date": date_str,
            "final_image_path": str(final_image_path),
        }

        if args.skip_existing and final_image_path.exists():
            manifest_entry["status"] = "skipped_existing"
            manifest.append(manifest_entry)
            print(f"[skip] {final_image_path}")
            continue

        raw_output_dir = raw_root / city_name / str(year) / sat_image_name.replace(".", "_")
        raw_output_dir.mkdir(parents=True, exist_ok=True)

        command = build_downloader_command(
            downloader_exe=args.downloader_exe,
            city_name=city_name,
            zoom_level=args.zoom_level,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lng=min_lng,
            max_lng=max_lng,
            raw_output_dir=raw_output_dir,
            date_str=date_str,
        )

        print("[run]", " ".join(command))
        subprocess.run(command, check=True)

        downloaded_image = find_downloaded_image(raw_output_dir, sat_image_name)
        if downloaded_image is None:
            raise FileNotFoundError(
                f"Could not locate downloaded image for `{sat_image_name}` under `{raw_output_dir}`. "
                "Please check downloader.exe output or metadata boundary values."
            )

        shutil.copy2(downloaded_image, final_image_path)
        manifest_entry["status"] = "downloaded"
        manifest_entry["raw_output_dir"] = str(raw_output_dir)
        manifest_entry["downloaded_image"] = str(downloaded_image)
        manifest.append(manifest_entry)
        print(f"[saved] {final_image_path}")

        if not args.keep_raw:
            shutil.rmtree(raw_output_dir, ignore_errors=True)

    manifest_path = args.output_dir / "metadata_sat_download_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[manifest] {manifest_path}")


if __name__ == "__main__":
    main()

