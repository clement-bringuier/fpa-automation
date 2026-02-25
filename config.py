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

# ── IFRS 16 ───────────────────────────────────────────────────────────────────

IFRS16_ENTITIES       = ["PID", "CELSIUS"]
IFRS16_LOYER_ACCOUNTS = {"PID": "61343", "CELSIUS": "61320"}

# ── Styles Excel (output_08) ──────────────────────────────────────────────────

C_HEADER   = "1F2D3D"   # Bleu nuit — header colonnes
C_SECTION  = "2E4057"   # Bleu foncé — sections (Revenue, EBITDA…)
C_SUBTOTAL = "4A90D9"   # Bleu moyen — sous-totaux (Gross Profit, CM…)
C_TOTAL    = "1ABC9C"   # Vert — totaux (EBIT, Net Income)
C_ROW_ALT  = "F5F7FA"   # Gris clair — lignes alternées
C_WHITE    = "FFFFFF"
C_WARN     = "E74C3C"   # Rouge — écarts intercos

# ── Structure P&L (output_08) ─────────────────────────────────────────────────
# Les valeurs "item" correspondent aux Mapping_PL_category du mapping_pcg.xlsx.

PL_STRUCTURE = [
    # (ligne, type)  type: 'item' | 'subtotal' | 'total' | 'section' | 'spacer'
    ("REVENUE",                  "section"),
    ("Sales",                    "item"),
    ("B2C Revenue",              "item"),
    ("B2B Revenue",              "item"),
    ("GROSS PROFIT",             "subtotal"),
    ("COGS",                     "item"),
    ("",                         "spacer"),
    ("Staff costs (Operating)",  "item"),
    ("Marketing costs",          "item"),
    ("Freelance",                "item"),
    ("Servers & softwares",      "item"),
    ("CONTRIBUTION MARGIN",      "subtotal"),
    ("Staff costs (Non-op.)",    "item"),
    ("Structure costs",          "item"),
    ("Accommodation costs",      "item"),
    ("Profit-sharing",           "item"),
    ("Rents & charges",          "item"),
    ("EBITDA",                   "total"),
    ("D&A on fixed assets",      "item"),
    ("D&A - Milestones",         "item"),
    ("D&A ROU (IFRS 16)",        "item"),
    ("EBIT",                     "total"),
    ("Financial income (loss)",  "item"),
    ("EBT",                      "subtotal"),
    ("Tax",                      "item"),
    ("NET INCOME",               "total"),
    ("Extraordinary items",      "item"),
]

# ── Groupes reporting (output_08) ─────────────────────────────────────────────

REPORTING_GROUPS = {
    "PID & FR"           : ["PID", "FR"],
    "CELSIUS & VERTICAL" : ["CELSIUS", "VERTICAL"],
    "Consolidé"          : ["FR", "PID", "CELSIUS", "VERTICAL"],
}