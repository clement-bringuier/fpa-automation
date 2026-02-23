"""
ifrs16_07.py — Retraitement IFRS 16
--------------------------------------
Logique :
  - Extrait les loyers comptabilisés (comptes 6132/6135) sur PID et CELSIUS
  - Neutralise le loyer de l'EBITDA (sortie des charges opérationnelles)
  - Enregistre un amortissement ROU en D&A (montant identique)
  - Impact EBIT = 0

Inputs :
  - df_fec  : DataFrame consolidé (depuis load_fec_01.py)
  - period  : str au format 'YYYYMM'

Output :
  - dict avec clés :
      'loyers_pid'      : float — loyer mensuel PID
      'loyers_celsius'  : float — loyer mensuel CELSIUS
      'rou_pid'         : float — amortissement ROU PID (= loyers_pid)
      'rou_celsius'     : float — amortissement ROU CELSIUS (= loyers_celsius)
      'df_ifrs16'       : DataFrame — détail pour output_08.py
"""

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Constantes ────────────────────────────────────────────────────────────────

LOYER_ACCOUNTS = {
    "PID":     "61343",
    "CELSIUS": "61320",
}
ENTITIES_IFRS16 = ("PID", "CELSIUS")


# ── Fonctions ─────────────────────────────────────────────────────────────────

def _extract_loyers(df_fec: pd.DataFrame, period: str, entity: str) -> float:
    """Extrait le loyer mensuel d'une entité depuis le FEC."""
    period_dt = pd.to_datetime(period, format="%Y%m").to_period("M")
    prefix = LOYER_ACCOUNTS[entity]
    mask = (
        df_fec["CompteNum"].astype(str).str.startswith(prefix)
        & (df_fec["EcritureDate"].dt.to_period("M") == period_dt)
        & (df_fec["Entite"] == entity)
    )
    df = df_fec[mask]
    loyer = (df["Debit"] - df["Credit"]).sum()
    return round(float(loyer), 2)


# ── Point d'entrée principal ───────────────────────────────────────────────────

def run(df_fec: pd.DataFrame, period: str) -> dict:

    loyers = {e: _extract_loyers(df_fec, period, e) for e in ENTITIES_IFRS16}

    df_ifrs16 = pd.DataFrame([
        {"Entite": e, "Ligne": "Loyer neutralisé (EBITDA)", "Montant": loyers[e]}
        for e in ENTITIES_IFRS16
    ] + [
        {"Entite": e, "Ligne": "Amortissement ROU (D&A)",   "Montant": -loyers[e]}
        for e in ENTITIES_IFRS16
    ])

    for e in ENTITIES_IFRS16:
        print(f"[ifrs16_07] {e} — Loyer : {loyers[e]:>10,.2f} € | ROU D&A : {-loyers[e]:>10,.2f} €")

    return {
        "loyers_pid":     loyers["PID"],
        "loyers_celsius": loyers["CELSIUS"],
        "rou_pid":        loyers["PID"],
        "rou_celsius":    loyers["CELSIUS"],
        "df_ifrs16":      df_ifrs16,
    }


# ── Test local ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.load_fec_01 import load_fec_entites, detect_periode

    INPUT_FOLDER = "data/fec"
    periode      = detect_periode(INPUT_FOLDER)
    df_fec       = load_fec_entites(INPUT_FOLDER, periode)

    result = run(df_fec, periode)

    print("\nDétail IFRS 16 :")
    print(result["df_ifrs16"].to_string(index=False))