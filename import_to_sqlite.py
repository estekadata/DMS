from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = Path("data")
DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "dms.sqlite"

def sanitize_table_name(stem: str) -> str:
    name = stem.strip()
    name = name.replace("tbl ", "tbl_").replace(" ", "_")
    name = (name.replace("é", "e").replace("è", "e").replace("ê", "e")
                .replace("à", "a").replace("ç", "c"))
    return name

def main():
    engine = create_engine(f"sqlite:///{DB_PATH}")

    files = sorted(DATA_DIR.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"Aucun .xlsx dans {DATA_DIR.resolve()}")

    for f in files:
        xl = pd.ExcelFile(f)
        sheet = xl.sheet_names[0]
        df = pd.read_excel(f, sheet_name=sheet, engine="openpyxl")

        table = sanitize_table_name(f.stem)
        df.to_sql(table, engine, if_exists="replace", index=False)
        print(f"✅ {f.name} -> {table} ({len(df)} lignes, {df.shape[1]} colonnes)")

    print(f"\nDB prête: {DB_PATH.resolve()}")

if __name__ == "__main__":
    main()

