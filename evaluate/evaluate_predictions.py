import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate benchmark predictions stored in the benchmark JSON itself or in a separate predictions file."
        )
    )
    parser.add_argument(
        "benchmark_json",
        type=Path,
        help="Path to a benchmark JSON file containing a list of samples.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=None,
        help=(
            "Optional predictions file. Supported formats: JSON object, JSON list, JSONL, or CSV. "
            "If omitted, the script reads the `prediction` field from the benchmark JSON."
        ),
    )
    parser.add_argument(
        "--id-key",
        default="ids",
        help="Sample id field name in the benchmark/predictions data. Default: ids",
    )
    parser.add_argument(
        "--reference-key",
        default="references",
        help="Ground-truth field name in the benchmark JSON. Default: references",
    )
    parser.add_argument(
        "--prediction-key",
        default="prediction",
        help="Prediction field name. Default: prediction",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to save aggregate metrics as JSON.",
    )
    parser.add_argument(
        "--output-per-sample",
        type=Path,
        default=None,
        help="Optional path to save merged per-sample evaluation records as JSON.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def coerce_float(value: Any) -> float:
    if value is None:
        raise ValueError("value is None")
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric prediction")
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty string")
        result = float(text)
    else:
        raise ValueError(f"unsupported numeric type: {type(value).__name__}")

    if math.isnan(result) or math.isinf(result):
        raise ValueError("prediction is NaN or Inf")
    return result


def load_predictions(path: Path, id_key: str, prediction_key: str) -> dict[str, float]:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return {
                str(row[id_key]): coerce_float(row[prediction_key])
                for row in reader
                if row.get(id_key) not in (None, "")
            }

    if suffix == ".jsonl":
        predictions: dict[str, float] = {}
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if id_key not in row:
                    raise KeyError(f"Missing `{id_key}` in JSONL line {line_no}.")
                predictions[str(row[id_key])] = coerce_float(row[prediction_key])
        return predictions

    data = load_json(path)

    if isinstance(data, dict):
        if all(not isinstance(v, dict) for v in data.values()):
            return {str(k): coerce_float(v) for k, v in data.items()}
        predictions = {}
        for key, value in data.items():
            if isinstance(value, dict):
                if prediction_key in value:
                    predictions[str(value.get(id_key, key))] = coerce_float(value[prediction_key])
                else:
                    raise KeyError(f"Missing `{prediction_key}` for prediction entry `{key}`.")
            else:
                predictions[str(key)] = coerce_float(value)
        return predictions

    if isinstance(data, list):
        predictions = {}
        for idx, row in enumerate(data):
            if not isinstance(row, dict):
                raise TypeError(f"Predictions JSON list item {idx} is not an object.")
            if id_key not in row:
                raise KeyError(f"Missing `{id_key}` in predictions JSON item {idx}.")
            predictions[str(row[id_key])] = coerce_float(row[prediction_key])
        return predictions

    raise TypeError("Unsupported predictions file format.")


def compute_rmse(y_true: list[float], y_pred: list[float]) -> float:
    mse = sum((pred - ref) ** 2 for ref, pred in zip(y_true, y_pred)) / len(y_true)
    return math.sqrt(mse)


def compute_r2(y_true: list[float], y_pred: list[float]) -> float:
    mean_true = sum(y_true) / len(y_true)
    ss_res = sum((ref - pred) ** 2 for ref, pred in zip(y_true, y_pred))
    ss_tot = sum((ref - mean_true) ** 2 for ref in y_true)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - (ss_res / ss_tot)


def main() -> None:
    args = parse_args()
    benchmark = load_json(args.benchmark_json)
    if not isinstance(benchmark, list):
        raise TypeError("Benchmark JSON must be a list of sample objects.")

    prediction_lookup = None
    if args.predictions is not None:
        prediction_lookup = load_predictions(args.predictions, args.id_key, args.prediction_key)

    y_true: list[float] = []
    y_pred: list[float] = []
    per_sample: list[dict[str, Any]] = []
    missing_predictions = 0
    invalid_predictions = 0

    for idx, sample in enumerate(benchmark):
        if not isinstance(sample, dict):
            raise TypeError(f"Benchmark item {idx} is not an object.")
        if args.id_key not in sample:
            raise KeyError(f"Missing `{args.id_key}` in benchmark item {idx}.")
        if args.reference_key not in sample:
            raise KeyError(f"Missing `{args.reference_key}` in benchmark item {idx}.")

        sample_id = str(sample[args.id_key])
        reference = coerce_float(sample[args.reference_key])

        raw_prediction: Any = None
        status = "ok"
        error_message = None

        if prediction_lookup is not None:
            if sample_id not in prediction_lookup:
                missing_predictions += 1
                status = "missing_prediction"
            else:
                raw_prediction = prediction_lookup[sample_id]
        else:
            if args.prediction_key not in sample:
                missing_predictions += 1
                status = "missing_prediction"
            else:
                raw_prediction = sample[args.prediction_key]

        prediction_value = None
        if status == "ok":
            try:
                prediction_value = coerce_float(raw_prediction)
            except Exception as exc:  # noqa: BLE001
                invalid_predictions += 1
                status = "invalid_prediction"
                error_message = str(exc)

        if status == "ok" and prediction_value is not None:
            y_true.append(reference)
            y_pred.append(prediction_value)

        per_sample.append(
            {
                args.id_key: sample_id,
                "reference": reference,
                "prediction": prediction_value,
                "status": status,
                "error": error_message,
                "city_name": sample.get("city_name"),
                "prompt": sample.get("prompt"),
                "images": sample.get("images"),
            }
        )

    if not y_true:
        raise ValueError("No valid predictions were found. Cannot compute metrics.")

    metrics = {
        "benchmark_json": str(args.benchmark_json),
        "predictions": str(args.predictions) if args.predictions else None,
        "num_total": len(benchmark),
        "num_scored": len(y_true),
        "num_missing_predictions": missing_predictions,
        "num_invalid_predictions": invalid_predictions,
        "rmse": compute_rmse(y_true, y_pred),
        "r2": compute_r2(y_true, y_pred),
    }

    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    if args.output_per_sample is not None:
        args.output_per_sample.parent.mkdir(parents=True, exist_ok=True)
        with args.output_per_sample.open("w", encoding="utf-8") as f:
            json.dump(per_sample, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
