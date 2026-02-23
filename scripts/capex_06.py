"""
capex_07.py — CAPEX cash milestones
-------------------------------------
Inputs :
  - period     : str au format 'YYYYMM' (période de clôture courante)
  - capex_file : chemin vers data/capex/capex_decaisses.xlsx
                 Colonnes attendues : Periode (YYYYMM) | Montant_decaisse

Output :
  - float : CAPEX décaissés du mois courant
"""

import pandas as pd
from pathlib import Path


# ── Constantes ────────────────────────────────────────────────────────────────

CAPEX_FILE_DEFAULT = Path("data/capex/capex_decaisses.xlsx")

COL_PERIOD = "Periode"
COL_AMOUNT = "Montant_decaisse"


# ── Point d'entrée principal ───────────────────────────────────────────────────

def run(
    period: str,
    capex_file: Path = CAPEX_FILE_DEFAULT,
) -> float:
    """Lit le fichier cumulatif et retourne le décaissé du mois courant."""
    df = pd.read_excel(capex_file, dtype={COL_PERIOD: str})
    df[COL_PERIOD] = df[COL_PERIOD].astype(str).str.strip()

    row = df[df[COL_PERIOD] == str(period)]

    if row.empty:
        print(f"[capex_07] ⚠️  Période {period} absente du fichier — montant = 0")
        return 0.0

    capex_decaisses = round(float(row[COL_AMOUNT].iloc[0]), 2)
    print(f"[capex_07] CAPEX décaissés {period} : {capex_decaisses:>12,.2f} €")
    return capex_decaisses