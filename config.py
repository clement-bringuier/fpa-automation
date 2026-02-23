"""
config.py — Configuration globale du pipeline FP&A
"""

# ── Entités ───────────────────────────────────────────────────────────────────

ENTITES = ['FR', 'PID', 'CELSIUS', 'VERTICAL']

# ── Dossiers ──────────────────────────────────────────────────────────────────

FOLDERS = {
    "fec"          : "data/fec",
    "rh"           : "data/rh",
    "revenue_cogs" : "data/revenue_cogs",
    "capex"        : "data/capex",
    "mapping"      : "mapping",
    "output"       : "data/output",
}

# ── Comptabilité ──────────────────────────────────────────────────────────────

CLASSES_BILAN      = ['1', '2', '3', '4', '5']   # Comptes de bilan
CLASSES_PL         = ['6', '7']                   # Comptes de P&L
JOURNAL_AN         = 'AN'                          # Code journal À Nouveaux
NA_VALUES          = ['NA', 'N/A', 'NAN', '']     # Valeurs nulles textuelles
SEUIL_ECART_INTERCO = 0.01                         # Seuil de tolérance écarts intercos (€)

# ── Split BU ──────────────────────────────────────────────────────────────────

BU_MAPPING_PID = {
    'DV'           : 'Publishing',
    'PID GAMES'    : 'Publishing',
    'DISTRIBUTION' : 'Distribution',
}

CELSIUS_B2C_BUS = ['MGG', 'RR', 'Autres B2C']
CELSIUS_B2B_BUS = ['B2B']

LIGNES_PL_CA   = ['SALES', 'B2B Revenue', 'B2C Revenue']
LIGNES_PL_COGS = ['COGS']

# ── CAPEX ─────────────────────────────────────────────────────────────────────

CAPEX_FILE     = "data/capex/capex_decaisses.xlsx"
CAPEX_COL_PERIOD = "Periode"
CAPEX_COL_AMOUNT = "Montant_decaisse"