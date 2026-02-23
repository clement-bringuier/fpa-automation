"""
ifrs16_07.py — Retraitement IFRS 16
--------------------------------------
Logique :
  - Extrait les loyers comptabilisés depuis le FEC (comptes par entité dans config)
  - Neutralise le loyer de l'EBITDA
  - Enregistre un amortissement ROU en D&A (montant identique)
  - Impact EBIT = 0

Inputs :
  - df_fec  : DataFrame consolidé (depuis load_fec_01.py)
  - period  : str au format 'YYYYMM'

Output :
  - dict avec clés :
      'loyers_pid'      : float
      'loyers_celsius'  : float
      'rou_pid'         : float
      'rou_celsius'     : float
      'df_ifrs16'       : DataFrame — détail pour output_08.py
"""

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import IFRS16_LOYER_ACCOUNTS, IFRS16_ENTITIES


def _extract_loyers(df_fec: pd.DataFrame, period: str, entity: str) -> float:
    period_dt = pd.to_datetime(period, format="%Y%m").to_period("M")
    prefix    = IFRS16_LOYER_ACCOUNTS[entity]
    mask = (
        df_fec["CompteNum"].astype(str).str.startswith(prefix)
        & (df_fec["EcritureDate"].dt.to_period("M") == period_dt)
        & (df_fec["Entite"] == entity)
    )
    return round(float((df_fec[mask]["Debit"] - df_fec[mask]["Credit"]).sum()), 2)


def run(df_fec: pd.DataFrame, period: str) -> dict:
    loyers = {e: _extract_loyers(df_fec, period, e) for e in IFRS16_ENTITIES}

    df_ifrs16 = pd.DataFrame(
        [{"Entite": e, "Ligne": "Loyer neutralisé (EBITDA)", "Montant":  loyers[e]} for e in IFRS16_ENTITIES] +
        [{"Entite": e, "Ligne": "Amortissement ROU (D&A)",   "Montant": -loyers[e]} for e in IFRS16_ENTITIES]
    )

    for e in IFRS16_ENTITIES:
        print(f"[ifrs16_07] {e} — Loyer : {loyers[e]:>10,.2f} € | ROU D&A : {-loyers[e]:>10,.2f} €")

    return {
        "loyers_pid":     loyers["PID"],
        "loyers_celsius": loyers["CELSIUS"],
        "rou_pid":        loyers["PID"],
        "rou_celsius":    loyers["CELSIUS"],
        "df_ifrs16":      df_ifrs16,
    }


if __name__ == "__main__":
    from config import FOLDERS
    from scripts.load_fec_01 import load_fec_entites, detect_periode

    periode = detect_periode(FOLDERS["fec"])
    df_fec  = load_fec_entites(FOLDERS["fec"], periode)
    result  = run(df_fec, periode)

    print("\nDétail IFRS 16 :")
    print(result["df_ifrs16"].to_string(index=False))