import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
MY_LABELS = HERE / "labels.jsonl"
INSTRUCTOR_LABELS = HERE / "reference" / "labels_instructor.jsonl"


def load_labels(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as file:
        return {row["id"]: row for row in map(json.loads, file)}


def main() -> None:
    mine = load_labels(MY_LABELS)
    instructor = load_labels(INSTRUCTOR_LABELS)
    differences = 0

    for label_id in sorted(mine.keys() | instructor.keys()):
        if label_id not in mine:
            print(f"#{label_id}: labels.jsonl に行がありません")
            differences += 1
            continue
        if label_id not in instructor:
            print(f"#{label_id}: labels_instructor.jsonl に行がありません")
            differences += 1
            continue

        mine_row, instructor_row = mine[label_id], instructor[label_id]
        for field in sorted(mine_row.keys() | instructor_row.keys()):
            mine_value = mine_row.get(field, "<なし>")
            instructor_value = instructor_row.get(field, "<なし>")
            if mine_value != instructor_value:
                print(f"#{label_id} {field}: 自分={mine_value!r} / 講師={instructor_value!r}")
                differences += 1

    print(f"差分: {differences} 件")


if __name__ == "__main__":
    main()