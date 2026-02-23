"""
main.py — Pipeline FP&A Automation
-------------------------------------
Ordre d'exécution :
  01 — Chargement et consolidation des FEC
  02 — Extraction mouvements P&L et soldes bilan
  03 — Application du mapping PCG
  04 — Éliminations intercompagnies
  05 — Split CA/COGS/masse salariale par BU
  06 — CAPEX cash milestones
  07 — Retraitement IFRS 16
  08 — Génération des reportings Excel
"""

from config                     import FOLDERS
from scripts.load_fec_01        import load_fec_entites, detect_periode
from scripts.monthly_movements_02 import (
    get_mouvements_mois,
    get_mouvements_par_compte,
    get_soldes_bilan,
)
from scripts.pcg_mapping_03     import (
    load_mapping_pcg,
    appliquer_mapping,
    agreger_pl,
    agreger_bilan,
)
from scripts.interco_04         import (
    load_interco,
    eliminer_intercos_pl,
    eliminer_intercos_bs,
)
from scripts.bu_split_05        import (
    load_split_ca_cogs,
    load_silae,
    load_mapping_rh,
    split_masse_salariale,
)
from scripts.capex_06           import run as run_capex
from scripts.ifrs16_07          import run as run_ifrs16
from scripts.output_08          import run as run_output


if __name__ == "__main__":

    # 01 — Chargement FEC
    periode = detect_periode(FOLDERS["fec"])
    df      = load_fec_entites(FOLDERS["fec"], periode)

    # 02 — Mouvements & soldes
    df_mois    = get_mouvements_mois(df, periode)
    df_comptes = get_mouvements_par_compte(df_mois)
    df_bilan   = get_soldes_bilan(df, periode)

    # 03 — Mapping PCG
    mappings              = load_mapping_pcg(FOLDERS["mapping"])
    df_mapped, df_alertes = appliquer_mapping(df_comptes, mappings)
    df_bilan_mapped       = agreger_bilan(df_bilan, mappings)

    # 04 — Éliminations intercos
    df_interco_pl, df_interco_bs    = load_interco(FOLDERS["mapping"])
    df_pl_elimine, recap_pl         = eliminer_intercos_pl(df_mois, df_mapped, df_interco_pl)
    df_bilan_elimine, recap_bs      = eliminer_intercos_bs(df, df_bilan, df_interco_bs)
    df_pl_final                     = agreger_pl(df_pl_elimine)

    # 05 — Split BU
    df_split      = load_split_ca_cogs(FOLDERS["revenue_cogs"], periode)
    df_silae      = load_silae(FOLDERS["rh"], periode)
    df_mapping_rh = load_mapping_rh(FOLDERS["rh"])
    df_opex_rh, df_capex_rh = split_masse_salariale(df_silae, df_mapping_rh)

    # 06 — CAPEX cash milestones
    capex_decaisses = run_capex(period=periode)

    # 07 — IFRS 16
    ifrs16 = run_ifrs16(df_fec=df, period=periode)

    # 08 — Output Excel
    run_output(
        df_pl_final     = df_pl_final,
        df_bilan_mapped = df_bilan_mapped,
        df_opex_rh      = df_opex_rh,
        recap_pl        = recap_pl,
        recap_bs        = recap_bs,
        ifrs16          = ifrs16,
        periode         = periode,
        output_folder   = FOLDERS["output"],
    )