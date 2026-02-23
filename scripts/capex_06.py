"""
capex_06.py — CAPEX cash milestones
-------------------------------------
Inputs :
  - period     : str au format 'YYYYMM' (période de clôture courante)
  - capex_file : chemin vers le fichier décaissés (défaut : config.CAPEX_FILE)

Output :
  - float : CAPEX décaissés du mois courant
"""

import pandas as pd
from pathlib import Path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CAPEX_FILE, CAPEX_COL_PERIOD, CAPEX_COL_AMOUNT


def run(period: str, capex_file: str = CAPEX_FILE) -> float:
    """Lit le fichier cumulatif et retourne le décaissé du mois courant."""
    df = pd.read_excel(capex_file, dtype={CAPEX_COL_PERIOD: str})
    df[CAPEX_COL_PERIOD] = df[CAPEX_COL_PERIOD].astype(str).str.strip()

    row = df[df[CAPEX_COL_PERIOD] == str(period)]

    if row.empty:
        print(f"[capex_06] ⚠️  Période {period} absente du fichier — montant = 0")
        return 0.0

    capex_decaisses = round(float(row[CAPEX_COL_AMOUNT].iloc[0]), 2)
    print(f"[capex_06] CAPEX décaissés {period} : {capex_decaisses:>12,.2f} €")
    return capex_decaisses