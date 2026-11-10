"""
------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------

    Single file:
        python combine_mteisp.py sample_1_R91_pH2_100uM.mteisp <output_folder>

    Whole folder (processes every .mteisp file found):
        python combine_mteisp.py <input_folder> <output_folder>

    Example:
        python combine_mteisp.py ~/raw_nova_exports \\
            ~/data/Matsvei/Polymerisation_Optimisation_TEG-S_EDOT/20260811_Batch
"""

import argparse
import html
import re
import sys
from pathlib import Path

# NOVA's fixed curve-type identifiers - verified consistent across multiple
# real .mteisp files in this project, more robust than parsing the
# auto-generated <name> string.
CURVE_TYPES = {
    "BODE_PHASE": "bodePhase",
    "BODE_Z_MOD": "bodeZmod",
    "NYQUIST": "nyquist",
}

# Which XML tags hold frequency / y-value for each curve type - NOVA reuses
# generic axis-slot tags (time/potential/i1) differently depending on curve
# type, confirmed by direct inspection of real files:
#   BODE_PHASE / BODE_Z_MOD : potential = frequency, i1 = y-value
#   NYQUIST                 : time = frequency, potential = Z', i1 = -Z''
FREQ_TAG = {"bodePhase": "potential", "bodeZmod": "potential", "nyquist": "time"}


def format_freq(value: float) -> str:
    """NOVA's own CSV export formats frequency with fixed 3 decimal places,
    zero-padded and never stripped (e.g. 287346.0 -> "287346.000").
    Confirmed against MB-001_1408's manual NOVA CSV export."""
    return f"{value:.3f}"


def format_value(value: float) -> str:
    """NOVA's own CSV export rounds phase/|Z|/Z'/-Z'' values to 6 decimal
    places, then prints with trailing zeros stripped (e.g. -6.0364966 ->
    "-6.036497", -2.7693 stays "-2.7693"). Python's default float string
    conversion after round(x, 6) reproduces this exactly - confirmed
    against 12/12 points in MB-001_1408's manual NOVA CSV export."""
    return str(round(value, 6))


def extract_curve_by_type(content: str, type_key: str):
    """Find the <curve> block whose <TypeEISCurve> matches type_key,
    return (curve_name, dict of tag -> list of float values)."""
    idx = content.find(f"<TypeEISCurve>{type_key}</TypeEISCurve>")
    if idx == -1:
        return None, None

    cstart = content.rfind("<curve>", 0, idx)
    cend = content.find("</curve>", idx)
    block = content[cstart:cend]

    name_match = re.search(r"<name>([^<]*)</name>", block)
    name = name_match.group(1) if name_match else "unknown"

    tags = {}
    for tag in ["time", "potential", "i1"]:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.DOTALL)
        if m:
            # Unescape XML entities (e.g. "&#13;" -> real carriage return)
            # BEFORE splitting on commas and converting to float - some
            # NOVA exports embed CR/LF or other entities inside the raw
            # numeric list, which breaks float() if left un-decoded.
            raw = html.unescape(m.group(1))
            tags[tag] = [float(v.strip()) for v in raw.split(",") if v.strip() != ""]
    return name, tags


def convert_file(input_file: Path, output_folder: Path) -> Path | None:
    content = input_file.read_text(encoding="utf-8")

    curves = {}
    for xml_type, section_key in CURVE_TYPES.items():
        name, tags = extract_curve_by_type(content, xml_type)
        if tags is None:
            print(f"  SKIPPING '{input_file.name}': no {xml_type} curve found")
            return None
        curves[section_key] = (name, tags)

    name_ph, tags_ph = curves["bodePhase"]
    name_zm, tags_zm = curves["bodeZmod"]
    name_ny, tags_ny = curves["nyquist"]

    freq_ph = tags_ph[FREQ_TAG["bodePhase"]]
    phase = tags_ph["i1"]

    freq_zm = tags_zm[FREQ_TAG["bodeZmod"]]
    zmod = tags_zm["i1"]

    freq_ny = tags_ny[FREQ_TAG["nyquist"]]
    zreal = tags_ny["potential"]
    zimagneg = tags_ny["i1"]

    n_ph, n_zm, n_ny = len(freq_ph), len(freq_zm), len(freq_ny)
    if not (n_ph == n_zm == n_ny):
        print(
            f"  WARNING '{input_file.name}': point count mismatch "
            f"(bodePhase={n_ph}, bodeZ={n_zm}, nyquist={n_ny}). "
            f"Truncating to shortest."
        )
    n = min(n_ph, n_zm, n_ny)

    lines = []

    lines.append(name_ph)
    lines.append("Freq (Hz);-Phase (deg)")
    for i in range(n):
        lines.append(f"{format_freq(freq_ph[i])};{format_value(phase[i])}")

    lines.append(name_zm)
    lines.append("Freq (Hz);|Z| (Ohm)")
    for i in range(n):
        lines.append(f"{format_freq(freq_zm[i])};{format_value(zmod[i])}")

    lines.append(name_ny)
    lines.append("Freq (Hz);Z' (Ohm);-Z'' (Ohm)")
    for i in range(n):
        lines.append(f"{format_freq(freq_ny[i])};{format_value(zreal[i])};{format_value(zimagneg[i])}")

    out_path = output_folder / f"{input_file.stem}.csv"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Wrote {out_path.name}  ({n} points x 3 sections)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert NOVA .mteisp file(s) into eis_fitting-compatible raw CSVs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_path", type=Path, help="A single .mteisp file OR a folder of them")
    parser.add_argument("output_folder", type=Path, help="Folder to write combined .csv files into")
    args = parser.parse_args()

    input_path: Path = args.input_path
    output_folder: Path = args.output_folder
    output_folder.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        mteisp_files = [input_path]
    elif input_path.is_dir():
        mteisp_files = sorted(input_path.glob("*.mteisp"))
        if not mteisp_files:
            print(f"No .mteisp files found in {input_path}")
            sys.exit(1)
    else:
        print(f"Input path not found: {input_path}")
        sys.exit(1)

    print(f"Found {len(mteisp_files)} .mteisp file(s):\n")

    written = []
    for f in mteisp_files:
        print(f"Processing '{f.name}':")
        result = convert_file(f, output_folder)
        if result is not None:
            written.append(result)
        print()

    print(f"Done. {len(written)}/{len(mteisp_files)} file(s) written successfully.")


if __name__ == "__main__":
    main()
