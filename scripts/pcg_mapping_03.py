import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ENTITES, CLASSES_PL, NA_VALUES


def load_mapping_pcg(mapping_folder):
    filepath = os.path.join(mapping_folder, 'mapping_pcg.xlsx')
    mappings = {}

    print("\nChargement du mapping PCG...")

    for entite in ENTITES:
        try:
            df = pd.read_excel(filepath, sheet_name=entite, dtype=str)
            df.columns = ['CompteNum', 'CompteLib', 'Mapping_PL_detail', 'Mapping_BS_detail',
                          'Mapping_PL_category', 'Mapping_BS_category']

            na_upper = [v.upper() for v in NA_VALUES]
            for col in ['CompteNum', 'Mapping_PL_detail', 'Mapping_BS_detail',
                        'Mapping_PL_category', 'Mapping_BS_category']:
                df[col] = df[col].str.strip()
                if col != 'CompteNum':
                    df[col] = df[col].where(~df[col].str.upper().isin(na_upper), other=None)

            mappings[entite] = df
            print(f"  {entite} : {len(df)} comptes chargés")

        except Exception as e:
            print(f"  {entite} : onglet non trouvé ou erreur — {e}")

    return mappings


def appliquer_mapping(df_comptes, mappings):
    dfs_mapped  = []
    dfs_alertes = []

    for entite, df_mapping in mappings.items():
        df_entite = df_comptes[df_comptes['Entite'] == entite].copy()
        if df_entite.empty:
            continue

        df_merged = df_entite.merge(
            df_mapping[['CompteNum', 'Mapping_PL_detail', 'Mapping_BS_detail',
                        'Mapping_PL_category', 'Mapping_BS_category']],
            on='CompteNum', how='left'
        )

        non_mappes = df_merged[df_merged['Mapping_PL_detail'].isna() & df_merged['Mapping_BS_detail'].isna()]
        if not non_mappes.empty:
            non_mappes = non_mappes.copy()
            non_mappes['Entite'] = entite
            dfs_alertes.append(non_mappes[['Entite', 'CompteNum', 'CompteLib', 'Mouvement']])
            print(f"\n  ⚠️  {entite} : {len(non_mappes)} compte(s) non mappé(s) !")
            print(non_mappes[['CompteNum', 'CompteLib']].to_string(index=False))

        dfs_mapped.append(df_merged)

    df_mapped  = pd.concat(dfs_mapped,  ignore_index=True) if dfs_mapped  else pd.DataFrame()
    df_alertes = pd.concat(dfs_alertes, ignore_index=True) if dfs_alertes else pd.DataFrame()

    if df_alertes.empty:
        print("\n  ✅ Tous les comptes sont mappés")

    return df_mapped, df_alertes


def agreger_pl(df_mapped):
    df_pl = df_mapped[
        df_mapped['ClasseCompte'].isin(CLASSES_PL) &
        df_mapped['Mapping_PL_detail'].notna()
    ].copy()

    pl = df_pl.groupby(['Entite', 'Mapping_PL_category', 'Mapping_PL_detail'], as_index=False).agg(
        Mouvement=('Mouvement', 'sum')
    )

    # Produits (classe 7) créditeurs en compta → on inverse pour affichage P&L
    pl['Mouvement'] = pl['Mouvement'] * -1

    print(f"\nP&L agrégé : {pl['Mapping_PL_detail'].nunique()} lignes de détail distinctes")
    return pl


def agreger_bilan(df_soldes_bilan, mappings):
    dfs = []

    for entite, df_mapping in mappings.items():
        df_entite = df_soldes_bilan[df_soldes_bilan['Entite'] == entite].copy()
        if df_entite.empty:
            continue
        df_merged = df_entite.merge(
            df_mapping[['CompteNum', 'Mapping_BS_category', 'Mapping_BS_detail']],
            on='CompteNum', how='left'
        )
        dfs.append(df_merged)

    df_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    bilan = df_all[df_all['Mapping_BS_detail'].notna()].groupby(
        ['Entite', 'Mapping_BS_category', 'Mapping_BS_detail'], as_index=False
    ).agg(Solde=('Solde', 'sum'))

    print(f"Bilan agrégé : {bilan['Mapping_BS_detail'].nunique()} lignes de détail distinctes")
    return bilan


if __name__ == "__main__":
    from config import FOLDERS
    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import (
        get_mouvements_mois, get_mouvements_par_compte, get_soldes_bilan
    )

    periode    = detect_periode(FOLDERS["fec"])
    df         = load_fec_entites(FOLDERS["fec"], periode)
    df_mois    = get_mouvements_mois(df, periode)
    df_comptes = get_mouvements_par_compte(df_mois)
    df_bilan   = get_soldes_bilan(df, periode)
    mappings   = load_mapping_pcg(FOLDERS["mapping"])

    df_mapped, df_alertes = appliquer_mapping(df_comptes, mappings)
    df_pl                 = agreger_pl(df_mapped)
    df_bilan_mapped       = agreger_bilan(df_bilan, mappings)

    print("\nAperçu P&L :")
    print(df_pl.to_string(index=False))
    print("\nAperçu Bilan :")
    print(df_bilan_mapped.to_string(index=False))