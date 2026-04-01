import json
import sys
from pathlib import Path


def pct(value: float) -> str:
    return f"{value:.2f}%"


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python scripts/generate_coverage_markdown.py "
            "<coverage.json> <summary.md> <details.md>"
        )
        return 1

    json_path = Path(sys.argv[1])
    summary_path = Path(sys.argv[2])
    details_path = Path(sys.argv[3])

    if not json_path.exists():
        print(f"Coverage JSON file not found: {json_path}")
        return 1

    with json_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    totals = payload.get("totals", {})
    files = payload.get("files", {})

    rows = []
    for file_name, data in sorted(files.items()):
        summary = data.get("summary", {})
        rows.append(
            {
                "file": file_name,
                "statements": summary.get("num_statements", 0),
                "missing": summary.get("missing_lines", 0),
                "branches": summary.get("num_branches", 0),
                "partial": summary.get("num_partial_branches", 0),
                "cover": float(summary.get("percent_covered", 0.0)),
                "missing_lines": data.get("missing_lines", []),
            }
        )

    summary_lines = [
        "# Coverage Summary",
        "",
        f"- Total statements: {totals.get('num_statements', 0)}",
        f"- Missing statements: {totals.get('missing_lines', 0)}",
        f"- Total branches: {totals.get('num_branches', 0)}",
        f"- Partial branches: {totals.get('num_partial_branches', 0)}",
        f"- Overall coverage: **{pct(float(totals.get('percent_covered', 0.0)))}**",
        "",
        "## Per-file Coverage",
        "",
        "| File | Stmts | Miss | Branch | BrPart | Cover |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        summary_lines.append(
            f"| {row['file']} | {row['statements']} | {row['missing']} | "
            f"{row['branches']} | {row['partial']} | {pct(row['cover'])} |"
        )

    detail_lines = [
        "# Coverage Missing Lines",
        "",
        "This report lists files that still have uncovered lines.",
        "",
    ]

    files_with_gaps = [r for r in rows if r["missing"] > 0]
    if not files_with_gaps:
        detail_lines.append("All tracked files are fully covered.")
    else:
        for row in files_with_gaps:
            detail_lines.append(f"## {row['file']}")
            detail_lines.append("")
            detail_lines.append(f"- Coverage: {pct(row['cover'])}")
            detail_lines.append(f"- Missing lines: {row['missing']}")
            missing = row["missing_lines"]
            if missing:
                # Keep markdown concise for CI summaries.
                preview = ", ".join(str(n) for n in missing[:60])
                suffix = " ..." if len(missing) > 60 else ""
                detail_lines.append(f"- Line numbers: {preview}{suffix}")
            detail_lines.append("")

    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    details_path.write_text("\n".join(detail_lines) + "\n", encoding="utf-8")

    print(f"Wrote {summary_path}")
    print(f"Wrote {details_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
