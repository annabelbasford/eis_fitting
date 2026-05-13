from pathlib import Path
import pandas as pd
from galvani import BioLogic

input_folder = Path("/home/abasford/projects/eis_fitting/mpr")
output_folder = Path("/home/abasford/projects/eis_fitting/csv/")
output_folder.mkdir(exist_ok=True)

for mpr_path in input_folder.glob("*.mpr"):
    print(f"Converting {mpr_path.name}")

    mpr = BioLogic.MPRfile(str(mpr_path))
    df = pd.DataFrame(mpr.data)

    csv_path = output_folder / f"{mpr_path.stem}.csv"
    df.to_csv(csv_path, index=False)

print("Done")