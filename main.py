import pathlib

import analyze
import fetch
import report


def main():
    raw = fetch.fetch_forecast()
    results = analyze.analyze(raw)
    html = report.render(results)

    out_dir = pathlib.Path(__file__).parent / "docs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
