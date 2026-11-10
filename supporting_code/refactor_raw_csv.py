"""
------------------------------------------------------------------------
TARGET LAYOUT (what the pipeline reads)
------------------------------------------------------------------------

Three sections, one below the other, semicolon-delimited, each preceded by a
marker line and a header row:

    i400sN1_1#006#bodePhase
    Freq (Hz);-Phase (deg)
    963279.250;31.36639
    ...
    i400sN1_1#007#bodeZmod
    Freq (Hz);|Z| (Ohm)
    ...
    i400sN1_1#008#nyquist
    Freq (Hz);Z' (Ohm);-Z'' (Ohm)
    ...

------------------------------------------------------------------------
WHAT IT DOES WITH EACH INPUT .csv (decided from the file contents)
------------------------------------------------------------------------

    converted   NOVA table export with the three blocks side by side on one
                row (nine columns: Freq, -Phase, spacer, Freq, |Z|, spacer,
                Z', -Z'', Freq). Rewritten into the target layout. Numbers are
                copied as text, never re-rounded.
    copied      Already in the target layout (quoted or unquoted). Copied
                byte for byte.
    skipped     Not an impedance spectrum in a raw layout. Always reported
                with the reason:
                  - empty file
                  - already-cleaned csv (header 'freq/Hz,Phase(Z)/deg,...':
                    pipeline output; use it as <experiment>/csv/ directly)
                  - fit-result table (header 'sample,circuit_name,...')
                  - Lissajous (time-domain) export
                  - unrecognised layout

An existing file in the output folder is never overwritten; it is reported
and skipped. Input files are never modified.

------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------

    Single file:
        python refactor_raw_csv.py sample.csv <output_folder>

    Folder (every .csv directly inside it):
        python refactor_raw_csv.py <input_folder> <output_folder>

    Folder tree (output mirrors the sub-folders; the output folder must not
    lie inside the input folder):
        python refactor_raw_csv.py <input_folder> <output_folder> -r

    Report what would happen without writing anything:
        python refactor_raw_csv.py <input_folder> <output_folder> -r --dry-run

    Example:
        python refactor_raw_csv.py "~/RAW EXPERIMENTAL DATA/EIS/Measurement 1208" \\
            ~/refactored/Measurement_1208 -r
"""

import argparse
import collections
import re
import shutil
import sys
from pathlib import Path

# marker suffix (lower case, after '#') -> section name used in the output
SECTIONS = ("bodephase", "bodezmod", "nyquist")
HEADER_ROWS = {
    "bodephase": "Freq (Hz);-Phase (deg)",
    "bodezmod": "Freq (Hz);|Z| (Ohm)",
    "nyquist": "Freq (Hz);Z' (Ohm);-Z'' (Ohm)",
}


def read_text(path: Path) -> str:
    """Decode as UTF-8 (a leading BOM is dropped); fall back to latin-1."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def norm_cell(cell: str) -> str:
    return cell.replace('"', "").strip()


def section_of(cell: str):
    """Section a marker cell announces ('...#bodePhase' etc.), else None."""
    low = cell.lower()
    for key in SECTIONS:
        if low.endswith("#" + key):
            return key
    return None


def parse_rows(text: str):
    """Rows of normalised cells; rows without any content are dropped."""
    rows = [[norm_cell(c) for c in line.split(";")] for line in text.splitlines()]
    return [r for r in rows if any(r)]


def classify(text: str):
    """Return (kind, reason); kind is 'convert', 'copy' or 'skip'."""
    rows = parse_rows(text)
    if not rows:
        return "skip", "empty file (no data lines)"

    first = [c for c in rows[0] if c]
    if first[0].startswith("freq/Hz,"):
        return "skip", "already-cleaned csv (pipeline output; use as <experiment>/csv/)"
    if first[0].startswith("sample,"):
        return "skip", "fit-result table, not a spectrum"
    if len(first) == 1 and first[0].lower().endswith("#lissajous"):
        return "skip", "Lissajous (time-domain) export, not an impedance spectrum"

    # sections stacked: marker lines that hold a single cell
    stacked = set()
    for r in rows:
        cells = [c for c in r if c]
        if len(cells) == 1 and section_of(cells[0]):
            stacked.add(section_of(cells[0]))
    if "bodephase" in stacked:
        return "copy", "already in the target layout"

    kinds = {section_of(c) for c in first}
    if set(SECTIONS) <= kinds:
        return "convert", "side-by-side blocks (NOVA table export)"
    return "skip", "unrecognised layout"


def convert_side_by_side(text: str, name: str):
    """Split a side-by-side NOVA table into the three stacked sections.
    Returns (output_text, warnings)."""
    warnings = []
    rows = parse_rows(text)

    marker = {}
    for c in rows[0]:
        sec = section_of(c) if c else None
        if sec:
            marker[sec] = c

    def squash(s):
        return re.sub(r"\s+", "", s).lower()

    hdr_i = next(
        (i for i, r in enumerate(rows[1:], 1) if any(squash(c).startswith("freq") for c in r)),
        None,
    )
    if hdr_i is None:
        raise ValueError("no header row with 'Freq' found")
    hdr = [squash(c) for c in rows[hdr_i]]

    def col(label):
        if label not in hdr:
            raise ValueError(f"column '{label}' not found in header {rows[hdr_i]}")
        return hdr.index(label)

    i_ph, i_zm = col("-phase(deg)"), col("|z|(ohm)")
    i_zr, i_zi = col("z'(ohm)"), col("-z''(ohm)")

    def freq_col(neighbour, step):
        j = neighbour + step
        if not (0 <= j < len(hdr)) or not hdr[j].startswith("freq"):
            raise ValueError(f"no 'Freq' column next to header column {neighbour}")
        return j

    f_ph = freq_col(i_ph, -1)
    f_zm = freq_col(i_zm, -1)
    f_ny = freq_col(i_zi, +1) if (i_zi + 1 < len(hdr) and hdr[i_zi + 1].startswith("freq")) else freq_col(i_zr, -1)

    data = rows[hdr_i + 1:]

    def block(cols):
        out = []
        for r in data:
            vals = [r[i] if i < len(r) else "" for i in cols]
            if all(v != "" for v in vals):
                for v in vals:
                    float(v)  # raises ValueError for non-numeric text
                out.append(vals)
        return out

    ph = block([f_ph, i_ph])
    zm = block([f_zm, i_zm])
    ny = block([f_ny, i_zr, i_zi])

    if not (len(ph) == len(zm) == len(ny)):
        warnings.append(f"point count differs between blocks (bodePhase={len(ph)}, bodeZmod={len(zm)}, nyquist={len(ny)}); kept as is")
    for k in range(min(len(ph), len(zm), len(ny))):
        f1, f2, f3 = float(ph[k][0]), float(zm[k][0]), float(ny[k][0])
        if abs(f1 - f2) > 1e-9 * abs(f1) or abs(f1 - f3) > 1e-9 * abs(f1):
            warnings.append(f"frequency differs between blocks at point {k + 1} ({f1}, {f2}, {f3})")
            break

    lines = []
    for sec, rows_ in (("bodephase", ph), ("bodezmod", zm), ("nyquist", ny)):
        lines.append(marker[sec])
        lines.append(HEADER_ROWS[sec])
        lines.extend(";".join(v) for v in rows_)
    return "\n".join(lines) + "\n", warnings


def collect(input_path: Path, recursive: bool):
    if input_path.is_file():
        return [input_path]
    pattern = "**/*.csv" if recursive else "*.csv"
    return sorted(p for p in input_path.glob(pattern) if p.is_file())


def main():
    parser = argparse.ArgumentParser(
        description="Bring raw Metrohm/NOVA .csv exports into the layout read by the eis_fitting pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_path", type=Path, help="A single .csv file OR a folder of them")
    parser.add_argument("output_folder", type=Path, help="Folder to write the .csv files into")
    parser.add_argument("-r", "--recursive", action="store_true", help="Also process sub-folders (output mirrors them)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would happen; write nothing")
    args = parser.parse_args()

    input_path = args.input_path.expanduser()
    output_folder = args.output_folder.expanduser()

    if not input_path.exists():
        print(f"Input path not found: {input_path}")
        sys.exit(1)
    if input_path.is_dir() and args.recursive:
        try:
            output_folder.resolve().relative_to(input_path.resolve())
            print("The output folder lies inside the input folder; choose a folder outside it.")
            sys.exit(1)
        except ValueError:
            pass

    files = collect(input_path, args.recursive)
    if not files:
        print(f"No .csv files found in {input_path}")
        sys.exit(1)
    base = input_path.parent if input_path.is_file() else input_path
    print(f"Found {len(files)} .csv file(s){' (dry run)' if args.dry_run else ''}\n")

    counts = collections.Counter()
    skipped = collections.defaultdict(list)
    for f in files:
        rel = f.relative_to(base)
        target = output_folder / (rel if args.recursive else Path(rel.name))
        kind, reason = classify(read_text(f))

        if kind == "skip":
            counts["skipped"] += 1
            skipped[reason].append(str(rel))
            continue
        if target.exists():
            counts["exists (not overwritten)"] += 1
            print(f"  EXISTS   {rel}  (not overwritten)")
            continue

        if kind == "copy":
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
            counts["copied"] += 1
            print(f"  COPIED   {rel}")
        else:
            try:
                out_text, warns = convert_side_by_side(read_text(f), f.name)
            except ValueError as exc:
                counts["failed"] += 1
                skipped[f"conversion failed: {exc}"].append(str(rel))
                continue
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(out_text, encoding="utf-8")
            counts["converted"] += 1
            print(f"  CONVERTED {rel}")
            for w in warns:
                print(f"      WARNING: {w}")

    if skipped:
        print("\nSkipped:")
        for reason, names in skipped.items():
            print(f"  {len(names):4d}  {reason}")
            for n in names[:5]:
                print(f"          {n}")
            if len(names) > 5:
                print(f"          ... and {len(names) - 5} more")

    print("\nSummary: " + ", ".join(f"{v} {k}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
