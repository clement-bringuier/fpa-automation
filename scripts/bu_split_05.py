import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BU_MAPPING_PID, CELSIUS_B2C_BUS, CELSIUS_B2B_BUS,
    LIGNES_PL_CA, LIGNES_PL_COGS
)


# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────

def load_split_ca_cogs(revenue_cogs_folder, periode):
    filepath = os.path.join(revenue_cogs_folder, 'split_ca_cogs.xlsx')
    df       = pd.read_excel(filepath, header=0).iloc[:, 1:]
    df.columns = ['Entite', 'Type', 'BU'] + list(df.columns[3:])
    df = df.dropna(subset=['Entite', 'BU'])

    # Colonnes dates uniquement
    date_cols = [c for c in df.columns if isinstance(c, pd.Timestamp)]
    df_long   = df.melt(id_vars=['Entite', 'Type', 'BU'], value_vars=date_cols,
                        var_name='Periode', value_name='Montant')

    target = pd.Timestamp(pd.to_datetime(periode, format='%Y%m'))
    df_long = df_long[df_long['Periode'] == target].copy()

    print(f"\nSplit CA/COGS chargé pour {periode} :")
    print(f"  Lignes : {len(df_long)}")
    print(df_long.to_string(index=False))
    return df_long


def load_silae(rh_folder, periode):
    print(f"\nChargement Silae pour {periode}...")
    dfs = []

    for f in os.listdir(rh_folder):
        if f.startswith(f'silae_{periode}_') and f.endswith('.xlsx'):
            entite   = f.replace(f'silae_{periode}_', '').replace('.xlsx', '').upper()
            filepath = os.path.join(rh_folder, f)

            df = pd.read_excel(filepath, header=2)[['Matricule', 'Salarié', 'Coût\nglobal']].copy()
            df.columns = ['Matricule', 'Salarie', 'Cout_global']
            df = df.dropna(subset=['Matricule', 'Cout_global'])
            df['Matricule']  = df['Matricule'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            df['Cout_global'] = pd.to_numeric(df['Cout_global'], errors='coerce').fillna(0)
            df['Entite']     = entite
            dfs.append(df)
            print(f"  {entite} : {len(df)} salariés chargés")

    df_silae = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    print(f"  Total : {len(df_silae)} salariés")
    return df_silae


def load_mapping_rh(rh_folder):
    filepath = os.path.join(rh_folder, 'mapping_rh.xlsx')
    df = pd.read_excel(filepath, header=0)
    df['Matricule'] = df['Matricule'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    print(f"\nMapping RH chargé : {len(df)} salariés")
    return df


# ─────────────────────────────────────────────
# SPLIT CA / COGS
# ─────────────────────────────────────────────

def split_ca_cogs(df_pl_final, df_split, type_flux):
    lignes_pl = LIGNES_PL_CA if type_flux == 'CA' else LIGNES_PL_COGS
    df_flux   = df_split[df_split['Type'] == type_flux].copy()
    resultats = []

    for entite in df_flux['Entite'].unique():
        df_ent        = df_flux[df_flux['Entite'] == entite]
        total_fichier = df_ent['Montant'].sum()
        if total_fichier == 0:
            continue

        total_compta = df_pl_final[
            (df_pl_final['Entite'] == entite) &
            (df_pl_final['Mapping_PL'].isin(lignes_pl))
        ]['Mouvement'].sum()

        print(f"\n  {entite} {type_flux} : compta={total_compta:,.2f} | fichier={total_fichier:,.2f}")

        for _, row in df_ent.iterrows():
            bu       = row['BU']
            bu_final = BU_MAPPING_PID.get(bu, bu)
            pct      = row['Montant'] / total_fichier
            print(f"    {bu} → {bu_final} : {pct:.1%} → {total_compta * pct:,.2f}")
            resultats.append({
                'Entite'    : entite,
                'BU'        : bu_final,
                'Mapping_PL': 'SALES' if type_flux == 'CA' else 'COGS',
                'Mouvement' : total_compta * pct
            })

    df_result = pd.DataFrame(resultats)
    if df_result.empty:
        return df_result

    return df_result.groupby(['Entite', 'BU', 'Mapping_PL'], as_index=False).agg(
        Mouvement=('Mouvement', 'sum')
    )


def split_celsius_ca(df_pl_final, df_split):
    df_celsius = df_split[(df_split['Entite'] == 'CELSIUS') & (df_split['Type'] == 'CA')].copy()

    ca_b2c = df_pl_final[(df_pl_final['Entite'] == 'CELSIUS') & (df_pl_final['Mapping_PL'] == 'B2C Revenue')]['Mouvement'].sum()
    ca_b2b = df_pl_final[(df_pl_final['Entite'] == 'CELSIUS') & (df_pl_final['Mapping_PL'] == 'B2B Revenue')]['Mouvement'].sum()

    total_b2c = df_celsius[df_celsius['BU'].isin(CELSIUS_B2C_BUS)]['Montant'].sum()
    total_b2b = df_celsius[df_celsius['BU'].isin(CELSIUS_B2B_BUS)]['Montant'].sum()

    resultats = []

    for _, row in df_celsius[df_celsius['BU'].isin(CELSIUS_B2C_BUS)].iterrows():
        pct = row['Montant'] / total_b2c if total_b2c != 0 else 0
        resultats.append({'Entite': 'CELSIUS', 'BU': row['BU'], 'Mapping_PL': 'B2C Revenue', 'Mouvement': ca_b2c * pct})

    resultats.append({'Entite': 'CELSIUS', 'BU': 'Total B2C', 'Mapping_PL': 'B2C Revenue', 'Mouvement': ca_b2c})

    for _, row in df_celsius[df_celsius['BU'].isin(CELSIUS_B2B_BUS)].iterrows():
        pct = row['Montant'] / total_b2b if total_b2b != 0 else 0
        resultats.append({'Entite': 'CELSIUS', 'BU': row['BU'], 'Mapping_PL': 'B2B Revenue', 'Mouvement': ca_b2b * pct})

    return pd.DataFrame(resultats)


# ─────────────────────────────────────────────
# SPLIT MASSE SALARIALE
# ─────────────────────────────────────────────

def split_masse_salariale(df_silae, df_mapping_rh):
    print("\nSplit masse salariale...")

    df = df_silae.merge(
        df_mapping_rh[['Matricule', 'BU', 'Type', 'IFRS', 'CAPEX %', 'OPEX %']],
        on='Matricule', how='left'
    )

    non_mappes = df[df['BU'].isna()]
    if not non_mappes.empty:
        print(f"  ⚠️  {len(non_mappes)} salarié(s) non mappé(s) :")
        print(non_mappes[['Matricule', 'Salarie', 'Entite']].to_string(index=False))

    df = df[df['BU'].notna()].copy()
    df['CAPEX %']    = pd.to_numeric(df['CAPEX %'], errors='coerce').fillna(0)
    df['OPEX %']     = pd.to_numeric(df['OPEX %'],  errors='coerce').fillna(1)
    df['Cout_CAPEX'] = df['Cout_global'] * df['CAPEX %']
    df['Cout_OPEX']  = df['Cout_global'] * df['OPEX %']

    df_opex = df.groupby(['Entite', 'BU', 'Type'], as_index=False).agg(Mouvement=('Cout_OPEX', 'sum'))
    df_opex['Mapping_PL'] = 'Staff costs'

    df_capex = df.groupby(['Entite', 'BU'], as_index=False).agg(Montant_CAPEX=('Cout_CAPEX', 'sum'))

    print(f"\n  OPEX masse salariale par BU :")
    print(df_opex.to_string(index=False))
    print(f"\n  CAPEX masse salariale par BU :")
    print(df_capex.to_string(index=False))

    return df_opex, df_capex


if __name__ == "__main__":
    from config import FOLDERS
    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import get_mouvements_mois, get_mouvements_par_compte, get_soldes_bilan
    from scripts.pcg_mapping_03 import load_mapping_pcg, appliquer_mapping, agreger_pl
    from scripts.interco_04 import load_interco, eliminer_intercos_pl

    periode          = detect_periode(FOLDERS["fec"])
    df               = load_fec_entites(FOLDERS["fec"], periode)
    df_mois          = get_mouvements_mois(df, periode)
    df_comptes       = get_mouvements_par_compte(df_mois)
    mappings         = load_mapping_pcg(FOLDERS["mapping"])
    df_mapped, _     = appliquer_mapping(df_comptes, mappings)
    df_interco_pl, _ = load_interco(FOLDERS["mapping"])
    df_pl_elimine, _ = eliminer_intercos_pl(df_mois, df_mapped, df_interco_pl)
    df_pl_final      = agreger_pl(df_pl_elimine)

    df_split      = load_split_ca_cogs(FOLDERS["revenue_cogs"], periode)
    df_silae      = load_silae(FOLDERS["rh"], periode)
    df_mapping_rh = load_mapping_rh(FOLDERS["rh"])
    df_opex_rh, df_capex_rh = split_masse_salariale(df_silae, df_mapping_rh)

    df_ca_pid     = split_ca_cogs(df_pl_final, df_split[df_split['Entite'] == 'PID'].copy(), 'CA')
    df_ca_celsius = split_celsius_ca(df_pl_final, df_split)
    df_cogs_pid   = split_ca_cogs(df_pl_final, df_split, 'COGS')

    print("\n=== CA par BU ===")
    print(pd.concat([df_ca_pid, df_ca_celsius]).to_string(index=False))
    print("\n=== COGS par BU ===")
    print(df_cogs_pid.to_string(index=False))
    print("\n=== Masse salariale OPEX par BU ===")
    print(df_opex_rh.to_string(index=False))