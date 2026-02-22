import pandas as pd
import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────
# CHARGEMENT
# ─────────────────────────────────────────────

def load_split_ca_cogs(revenue_cogs_folder, periode):
    """
    Charge le fichier de split CA/COGS
    Retourne un DataFrame en format long avec colonnes :
    Entite, Type, BU, Periode, Montant
    """
    filepath = os.path.join(revenue_cogs_folder, 'split_ca_cogs.xlsx')

    df = pd.read_excel(filepath, header=0)

    # Suppression colonne vide A (première colonne)
    df = df.iloc[:, 1:]
    df.columns = ['Entite', 'Type', 'BU'] + list(df.columns[3:])

    # Suppression ligne vide éventuelle
    df = df.dropna(subset=['Entite', 'BU'])

    # Conversion en format long
    date_cols = [c for c in df.columns if isinstance(c, (pd.Timestamp, datetime.datetime))]
    df_long = df.melt(
        id_vars=['Entite', 'Type', 'BU'],
        value_vars=date_cols,
        var_name='Periode',
        value_name='Montant'
    )

    # Filtre sur la période demandée
    df_long['Periode'] = pd.to_datetime(df_long['Periode'])
    target_ts = pd.Timestamp(pd.to_datetime(periode, format='%Y%m'))
    df_long = df_long[df_long['Periode'] == target_ts].copy()

    print(f"\nSplit CA/COGS chargé pour {periode} :")
    print(f"  Lignes : {len(df_long)}")
    print(df_long.to_string(index=False))

    return df_long


def load_silae(rh_folder, periode):
    """
    Charge et consolide les fichiers Silae de toutes les entités
    Retourne DataFrame avec Matricule, Salarié, Entite, Coût global
    """
    print(f"\nChargement Silae pour {periode}...")
    dfs = []

    for f in os.listdir(rh_folder):
        pattern = f'silae_{periode}_'
        if f.startswith(pattern) and f.endswith('.xlsx'):
            entite = f.replace(pattern, '').replace('.xlsx', '').upper()
            filepath = os.path.join(rh_folder, f)

            df = pd.read_excel(filepath, header=2)
            df = df[['Matricule', 'Salarié', 'Coût\nglobal']].copy()
            df.columns = ['Matricule', 'Salarie', 'Cout_global']
            df = df.dropna(subset=['Matricule', 'Cout_global'])

            # Nettoyage matricule : supprime .0 pour les numériques
            df['Matricule'] = df['Matricule'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            df['Cout_global'] = pd.to_numeric(df['Cout_global'], errors='coerce').fillna(0)
            df['Entite'] = entite
            dfs.append(df)
            print(f"  {entite} : {len(df)} salariés chargés")

    df_silae = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    print(f"  Total : {len(df_silae)} salariés")
    return df_silae


def load_mapping_rh(rh_folder):
    """
    Charge le fichier de mapping RH
    Colonnes : Matricule, Nom Prénom, BU, Type, IFRS, CAPEX %, OPEX %
    """
    filepath = os.path.join(rh_folder, 'mapping_rh.xlsx')
    df = pd.read_excel(filepath, header=0)

    # Nettoyage matricule : supprime .0 pour les numériques
    df['Matricule'] = df['Matricule'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    print(f"\nMapping RH chargé : {len(df)} salariés")
    return df


# ─────────────────────────────────────────────
# SPLIT CA / COGS
# ─────────────────────────────────────────────

def split_ca_cogs(df_pl_final, df_split, type_flux):
    """
    Applique le prorata BU sur le CA ou COGS compta

    Args:
        df_pl_final : P&L après éliminations intercos (sortie script 04)
        df_split    : DataFrame split CA/COGS (format long)
        type_flux   : 'CA' ou 'COGS'

    Returns:
        DataFrame avec colonnes Entite, BU, Mapping_PL, Mouvement
    """

    if type_flux == 'CA':
        lignes_pl = ['SALES', 'B2B Revenue', 'B2C Revenue']
    else:
        lignes_pl = ['COGS']

    df_flux = df_split[df_split['Type'] == type_flux].copy()
    resultats = []

    for entite in df_flux['Entite'].unique():
        df_ent = df_flux[df_flux['Entite'] == entite]
        total_fichier = df_ent['Montant'].sum()

        if total_fichier == 0:
            continue

        # CA/COGS compta pour cette entité
        masque_pl = (
            (df_pl_final['Entite'] == entite) &
            (df_pl_final['Mapping_PL'].isin(lignes_pl))
        )
        total_compta = df_pl_final[masque_pl]['Mouvement'].sum()

        print(f"\n  {entite} {type_flux} : compta={total_compta:,.2f} | fichier={total_fichier:,.2f}")

        for _, row in df_ent.iterrows():
            bu  = row['BU']
            pct = row['Montant'] / total_fichier
            montant_bu = total_compta * pct

            # Regroupement Publishing pour PID
            bu_final = bu
            if bu in ['DV', 'PID GAMES']:
                bu_final = 'Publishing'
            elif bu == 'DISTRIBUTION':
                bu_final = 'Distribution'

            print(f"    {bu} → {bu_final} : {pct:.1%} → {montant_bu:,.2f}")

            resultats.append({
                'Entite'     : entite,
                'BU'         : bu_final,
                'BU_detail'  : bu,
                'Mapping_PL' : 'SALES' if type_flux == 'CA' else 'COGS',
                'Mouvement'  : montant_bu
            })

    df_result = pd.DataFrame(resultats)

    if df_result.empty:
        return df_result

    # Agrégation Publishing (fusion DV + PID GAMES)
    df_result = df_result.groupby(
        ['Entite', 'BU', 'Mapping_PL'], as_index=False
    ).agg(Mouvement=('Mouvement', 'sum'))

    return df_result


def split_celsius_ca(df_pl_final, df_split):
    """
    Split CA CELSIUS avec détail B2C (MGG, RR, Autres B2C) + Total B2C + B2B
    """
    df_celsius = df_split[
        (df_split['Entite'] == 'CELSIUS') &
        (df_split['Type'] == 'CA')
    ].copy()

    b2c_bus = ['MGG', 'RR', 'Autres B2C']
    b2b_bus = ['B2B']

    ca_b2c_compta = df_pl_final[
        (df_pl_final['Entite'] == 'CELSIUS') &
        (df_pl_final['Mapping_PL'] == 'B2C Revenue')
    ]['Mouvement'].sum()

    ca_b2b_compta = df_pl_final[
        (df_pl_final['Entite'] == 'CELSIUS') &
        (df_pl_final['Mapping_PL'] == 'B2B Revenue')
    ]['Mouvement'].sum()

    total_b2c_fichier = df_celsius[df_celsius['BU'].isin(b2c_bus)]['Montant'].sum()
    total_b2b_fichier = df_celsius[df_celsius['BU'].isin(b2b_bus)]['Montant'].sum()

    resultats = []

    # Détail B2C
    for _, row in df_celsius[df_celsius['BU'].isin(b2c_bus)].iterrows():
        pct = row['Montant'] / total_b2c_fichier if total_b2c_fichier != 0 else 0
        resultats.append({
            'Entite'     : 'CELSIUS',
            'BU'         : row['BU'],
            'Mapping_PL' : 'B2C Revenue',
            'Mouvement'  : ca_b2c_compta * pct
        })

    # Total B2C
    resultats.append({
        'Entite'     : 'CELSIUS',
        'BU'         : 'Total B2C',
        'Mapping_PL' : 'B2C Revenue',
        'Mouvement'  : ca_b2c_compta
    })

    # B2B
    for _, row in df_celsius[df_celsius['BU'].isin(b2b_bus)].iterrows():
        pct = row['Montant'] / total_b2b_fichier if total_b2b_fichier != 0 else 0
        resultats.append({
            'Entite'     : 'CELSIUS',
            'BU'         : row['BU'],
            'Mapping_PL' : 'B2B Revenue',
            'Mouvement'  : ca_b2b_compta * pct
        })

    return pd.DataFrame(resultats)


# ─────────────────────────────────────────────
# SPLIT MASSE SALARIALE
# ─────────────────────────────────────────────

def split_masse_salariale(df_silae, df_mapping_rh):
    """
    Répartit la masse salariale par BU, catégorie et CAPEX/OPEX

    Returns:
        df_opex  : charges P&L par Entite, BU, Type (Operating/Non-operating)
        df_capex : montants activés au bilan par Entite, BU
    """
    print("\nSplit masse salariale...")

    df = df_silae.merge(
        df_mapping_rh[['Matricule', 'BU', 'Type', 'IFRS', 'CAPEX %', 'OPEX %']],
        on='Matricule',
        how='left'
    )

    # Salariés non mappés
    non_mappes = df[df['BU'].isna()]
    if not non_mappes.empty:
        print(f"  ⚠️  {len(non_mappes)} salarié(s) non mappé(s) :")
        print(non_mappes[['Matricule', 'Salarie', 'Entite']].to_string(index=False))

    df = df[df['BU'].notna()].copy()
    df['CAPEX %'] = pd.to_numeric(df['CAPEX %'], errors='coerce').fillna(0)
    df['OPEX %']  = pd.to_numeric(df['OPEX %'],  errors='coerce').fillna(1)

    df['Cout_CAPEX'] = df['Cout_global'] * df['CAPEX %']
    df['Cout_OPEX']  = df['Cout_global'] * df['OPEX %']

    # OPEX → P&L
    df_opex = df.groupby(
        ['Entite', 'BU', 'Type'], as_index=False
    ).agg(Mouvement=('Cout_OPEX', 'sum'))
    df_opex['Mapping_PL'] = 'Staff costs'

    # CAPEX → bilan
    df_capex = df.groupby(
        ['Entite', 'BU'], as_index=False
    ).agg(Montant_CAPEX=('Cout_CAPEX', 'sum'))

    print(f"\n  OPEX masse salariale par BU :")
    print(df_opex.to_string(index=False))
    print(f"\n  CAPEX masse salariale par BU :")
    print(df_capex.to_string(index=False))

    return df_opex, df_capex


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":

    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import get_mouvements_mois, get_mouvements_par_compte, get_soldes_bilan
    from scripts.pcg_mapping_03 import load_mapping_pcg, appliquer_mapping, agreger_pl
    from scripts.interco_04 import load_interco, eliminer_intercos_pl

    INPUT_FOLDER        = "data/fec"
    MAPPING_FOLDER      = "mapping"
    RH_FOLDER           = "data/rh"
    REVENUE_COGS_FOLDER = "data/revenue_cogs"

    # Pipeline scripts 01 → 04
    PERIODE          = detect_periode(INPUT_FOLDER)
    df               = load_fec_entites(INPUT_FOLDER, PERIODE)
    df_mois          = get_mouvements_mois(df, PERIODE)
    df_comptes       = get_mouvements_par_compte(df_mois)
    df_bilan         = get_soldes_bilan(df, PERIODE)
    mappings         = load_mapping_pcg(MAPPING_FOLDER)
    df_mapped, _     = appliquer_mapping(df_comptes, mappings)
    df_interco_pl, _ = load_interco(MAPPING_FOLDER)
    df_pl_elimine, _ = eliminer_intercos_pl(df_mois, df_mapped, df_interco_pl)
    df_pl_final      = agreger_pl(df_pl_elimine)

    # Script 05 — Split BU
    df_split      = load_split_ca_cogs(REVENUE_COGS_FOLDER, PERIODE)
    df_silae      = load_silae(RH_FOLDER, PERIODE)
    df_mapping_rh = load_mapping_rh(RH_FOLDER)

    # Split CA PID uniquement (CELSIUS géré séparément)
    df_split_pid  = df_split[df_split['Entite'] == 'PID'].copy()
    df_ca_pid     = split_ca_cogs(df_pl_final, df_split_pid, 'CA')

    # Split CA CELSIUS (détail B2C + B2B)
    df_ca_celsius = split_celsius_ca(df_pl_final, df_split)

    # Split COGS PID
    df_cogs_pid = split_ca_cogs(df_pl_final, df_split, 'COGS')

    # Split masse salariale
    df_opex_rh, df_capex_rh = split_masse_salariale(df_silae, df_mapping_rh)

    print("\n=== CA par BU ===")
    print(pd.concat([df_ca_pid, df_ca_celsius]).to_string(index=False))

    print("\n=== COGS par BU ===")
    print(df_cogs_pid.to_string(index=False))

    print("\n=== Masse salariale OPEX par BU ===")
    print(df_opex_rh.to_string(index=False))