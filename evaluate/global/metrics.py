import argparse
import base64
import json
import math
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 180
FLOAT_PATTERN = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
TASK_TYPE_TO_SUBSTRING = {
    "single": "single_year",
    "multi_year_type1": "multi_year_type1",
    "multi_year_type3": "multi_year_type3",
}
SAT_PATH_PATTERN = re.compile(r"downloaded_sat_(?P<year>\d+)_zoom_\d+/(?P<city_name>[^/]+)/[^/]+/[^/]+/[^/]+/[^/]+/(?P<sat_image_name>[^/]+)$")
STV_PATH_PATTERN = re.compile(r"downloaded_stv_selected/(?P<city_name>[^/]+)/(?P<identifier>[^/]+)/street_view_images/(?P<image_name>[^/]+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OpenRouter evaluation for an UrbanWell benchmark task and compute R2/RMSE."
    )
    parser.add_argument("--model_name", required=True, help="OpenRouter model name, e.g. openai/gpt-4o")
    parser.add_argument(
        "--task_type",
        required=True,
        choices=["single", "multi_year_type1", "multi_year_type3"],
        help="Benchmark task type.",
    )
    parser.add_argument("--task_name", required=True, help="Indicator/task name, e.g. population or NO2")
    parser.add_argument(
        "--benchmark_dir",
        default=None,
        help="Benchmark JSON directory. Defaults to benchmark_dataset_rewritten if it exists, otherwise benchmark_dataset.",
    )
    parser.add_argument(
        "--results_root",
        default="evaluate/results",
        help="Directory used to store model outputs and summaries. Default: evaluate/results",
    )
    parser.add_argument(
        "--existing_mode",
        default="reuse",
        choices=["reuse", "missing", "rerun"],
        help="How to handle existing prediction files. Default: reuse",
    )
    parser.add_argument(
        "--api_key",
        default=None,
        help="OpenRouter API key. If omitted, OPENROUTER_API_KEY is used.",
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Optional limit for debugging. Evaluate only the first N samples.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds. Default: 180",
    )
    return parser.parse_args()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_benchmark_dir(root: Path) -> Path:
    rewritten = root / "benchmark_dataset_rewritten"
    if rewritten.exists():
        return rewritten
    return root / "benchmark_dataset"


def sanitize_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def find_benchmark_file(benchmark_dir: Path, task_name: str, task_type: str) -> Path:
    if task_type not in TASK_TYPE_TO_SUBSTRING:
        raise ValueError("Unsupported task_type: {}".format(task_type))

    type_substring = TASK_TYPE_TO_SUBSTRING[task_type]
    expected_names = []
    if task_type == "single":
        expected_names.append("{}_single_year_final_500.json".format(task_name))
    else:
        expected_names.append("{}_{}_stv_num_4_year_num_4_final_500.json".format(task_name, task_type))
        expected_names.append("{}_{}_stv_num_4_year_num_2_final_500.json".format(task_name, task_type))

    for expected_name in expected_names:
        candidate = benchmark_dir / expected_name
        if candidate.exists():
            return candidate

    candidates = []
    for path in sorted(benchmark_dir.glob("*.json")):
        name = path.name
        if not name.startswith(task_name + "_"):
            continue
        if type_substring not in name:
            continue
        candidates.append(path)

    if not candidates:
        raise FileNotFoundError(
            "Could not find benchmark file for task_name={} task_type={} under {}".format(
                task_name, task_type, benchmark_dir
            )
        )
    if len(candidates) > 1:
        raise RuntimeError(
            "Multiple benchmark files match task_name={} task_type={}: {}".format(
                task_name,
                task_type,
                ", ".join(path.name for path in candidates),
            )
        )
    return candidates[0]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def coerce_float(value: Any) -> float:
    if value is None:
        raise ValueError("value is None")
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        result = float(value.strip())
    else:
        raise ValueError("unsupported numeric type: {}".format(type(value).__name__))
    if math.isnan(result) or math.isinf(result):
        raise ValueError("value is NaN or Inf")
    return result


def extract_numeric_prediction(text: str) -> float:
    matches = FLOAT_PATTERN.findall(text)
    if not matches:
        raise ValueError("No numeric value found in model output: {}".format(text))
    return coerce_float(matches[0])


def resolve_local_path(image_path: str, root: Path, benchmark_path: Path) -> Path:
    normalized = image_path.replace('\\', '/')
    raw = Path(image_path)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(root / raw)
        candidates.append(benchmark_path.parent / raw)
        candidates.append(Path.cwd() / raw)

    sat_match = SAT_PATH_PATTERN.search(normalized)
    if sat_match:
        candidates.append(root / 'sat-image' / sat_match.group('year') / sat_match.group('city_name') / sat_match.group('sat_image_name'))

    stv_match = STV_PATH_PATTERN.search(normalized)
    if stv_match:
        candidates.append(root / 'stv-image' / stv_match.group('city_name') / stv_match.group('identifier') / 'street_view_images' / stv_match.group('image_name'))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Image file not found for path: {}".format(image_path))


def local_image_to_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return "data:{};base64,{}".format(mime_type, encoded)


def build_user_content(sample: Dict[str, Any], root: Path, benchmark_path: Path) -> List[Dict[str, Any]]:
    content = [{"type": "text", "text": sample["prompt"]}]
    for image_path in sample.get("images", []):
        resolved = resolve_local_path(str(image_path), root, benchmark_path)
        data_url = local_image_to_data_url(resolved)
        content.append({"type": "image_url", "image_url": {"url": data_url}})
    return content


def call_openrouter(model_name: str, sample: Dict[str, Any], api_key: str, timeout: int, root: Path, benchmark_path: Path) -> Dict[str, Any]:
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": build_user_content(sample, root, benchmark_path),
            }
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": "Bearer {}".format(api_key),
        "Content-Type": "application/json",
    }
    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def extract_response_text(response_json: Dict[str, Any]) -> str:
    choices = response_json.get("choices", [])
    if not choices:
        raise ValueError("OpenRouter response does not contain choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(part for part in text_parts if part).strip()
    raise ValueError("Unsupported OpenRouter response content format")


def compute_rmse(y_true: List[float], y_pred: List[float]) -> float:
    mse = sum((pred - ref) ** 2 for ref, pred in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)


def compute_r2(y_true: List[float], y_pred: List[float]) -> float:
    mean_true = sum(y_true) / len(y_true)
    ss_res = sum((ref - pred) ** 2 for ref, pred in zip(y_true, y_pred))
    ss_tot = sum((ref - mean_true) ** 2 for ref in y_true)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - (ss_res / ss_tot)


def compute_summary(records: List[Dict[str, Any]], benchmark_file: Path, model_name: str, task_name: str, task_type: str) -> Dict[str, Any]:
    y_true = []
    y_pred = []
    missing = 0
    invalid = 0
    for record in records:
        if record.get("status") != "ok":
            if record.get("status") == "missing_prediction":
                missing += 1
            else:
                invalid += 1
            continue
        try:
            y_true.append(coerce_float(record.get("reference")))
            y_pred.append(coerce_float(record.get("prediction")))
        except Exception:
            invalid += 1

    if not y_true:
        raise ValueError("No valid predictions were found. Cannot compute metrics.")

    return {
        "benchmark_file": str(benchmark_file),
        "model_name": model_name,
        "task_name": task_name,
        "task_type": task_type,
        "num_total": len(records),
        "num_scored": len(y_true),
        "num_missing_predictions": missing,
        "num_invalid_predictions": invalid,
        "rmse": compute_rmse(y_true, y_pred),
        "r2": compute_r2(y_true, y_pred),
    }


def load_existing_records(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    if not isinstance(data, list):
        raise TypeError("Existing predictions file must contain a list of records: {}".format(path))
    records = {}
    for item in data:
        if isinstance(item, dict) and "ids" in item:
            records[str(item["ids"])] = item
    return records


def main() -> None:
    args = parse_args()
    root = project_root()
    benchmark_dir = Path(args.benchmark_dir) if args.benchmark_dir else default_benchmark_dir(root)
    benchmark_dir = benchmark_dir if benchmark_dir.is_absolute() else root / benchmark_dir
    benchmark_file = find_benchmark_file(benchmark_dir, args.task_name, args.task_type)

    benchmark = load_json(benchmark_file)
    if not isinstance(benchmark, list):
        raise TypeError("Benchmark JSON must contain a list of samples: {}".format(benchmark_file))
    if args.max_samples is not None:
        benchmark = benchmark[: args.max_samples]

    safe_model = sanitize_name(args.model_name)
    result_dir = root / args.results_root / safe_model / args.task_type / args.task_name
    predictions_path = result_dir / "predictions.json"
    summary_path = result_dir / "summary.json"

    existing_records = {}
    if args.existing_mode in ("reuse", "missing") and predictions_path.exists():
        existing_records = load_existing_records(predictions_path)

    if args.existing_mode == "reuse" and predictions_path.exists():
        records = [existing_records[str(sample["ids"])] for sample in benchmark if str(sample["ids"]) in existing_records]
        summary = compute_summary(records, benchmark_file, args.model_name, args.task_name, args.task_type)
        save_json(summary_path, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OpenRouter API key is required. Pass --api_key or set OPENROUTER_API_KEY.")

    records = []
    updated_records = dict(existing_records) if args.existing_mode == "missing" else {}

    for index, sample in enumerate(benchmark):
        if not isinstance(sample, dict):
            continue
        sample_id = str(sample["ids"])
        reference = sample.get("references")

        if args.existing_mode == "missing" and sample_id in updated_records:
            existing = updated_records[sample_id]
            if existing.get("status") == "ok" and existing.get("prediction") is not None:
                records.append(existing)
                continue

        record = {
            "ids": sample_id,
            "reference": reference,
            "prediction": None,
            "status": "pending",
            "error": None,
            "raw_model_output": None,
            "model_name": args.model_name,
            "task_name": args.task_name,
            "task_type": args.task_type,
        }

        try:
            response_json = call_openrouter(
                model_name=args.model_name,
                sample=sample,
                api_key=api_key,
                timeout=args.timeout,
                root=root,
                benchmark_path=benchmark_file,
            )
            raw_output = extract_response_text(response_json)
            prediction = extract_numeric_prediction(raw_output)
            record["prediction"] = prediction
            record["raw_model_output"] = raw_output
            record["status"] = "ok"
            record["response_id"] = response_json.get("id")
            record["usage"] = response_json.get("usage")
        except Exception as exc:
            record["status"] = "error"
            record["error"] = str(exc)

        updated_records[sample_id] = record
        records = [updated_records[str(item["ids"])] for item in benchmark if str(item["ids"]) in updated_records]
        save_json(predictions_path, records)
        print("[{}/{}] {} -> {}".format(index + 1, len(benchmark), sample_id, record["status"]))

    records = [updated_records[str(sample["ids"])] for sample in benchmark if str(sample["ids"]) in updated_records]
    save_json(predictions_path, records)
    summary = compute_summary(records, benchmark_file, args.model_name, args.task_name, args.task_type)
    save_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


