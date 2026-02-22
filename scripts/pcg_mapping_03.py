import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_mapping_pcg(mapping_folder):
    """
    Charge le fichier de mapping PCG pour toutes les entités

    Args:
        mapping_folder : chemin vers le dossier mapping/

    Returns:
        Dictionnaire {nom_entite: DataFrame mapping}
    """

    filepath = os.path.join(mapping_folder, 'mapping_pcg.xlsx')
    entites_valides = ['FR', 'PID', 'CELSIUS', 'VERTICAL']
    mappings = {}

    print("\nChargement du mapping PCG...")

    for entite in entites_valides:
        try:
            df = pd.read_excel(filepath, sheet_name=entite, dtype=str)

            # Nettoyage des colonnes
            df.columns = df.columns.str.strip()

            # Renommage des colonnes pour uniformiser
            # Colonnes attendues : Numéro, Intitulé, Mapping P&L, Mapping BS
            df.columns = ['CompteNum', 'CompteLib', 'Mapping_PL', 'Mapping_BS']

            # Nettoyage des valeurs
            df['CompteNum']  = df['CompteNum'].str.strip()
            df['Mapping_PL'] = df['Mapping_PL'].str.strip()
            df['Mapping_BS'] = df['Mapping_BS'].str.strip()

            # Traitement des "NA" textuels → vraie valeur nulle
            df['Mapping_PL'] = df['Mapping_PL'].apply(lambda x: None if str(x).upper().strip() in ['NA', 'N/A', 'NAN', ''] else x)
            df['Mapping_BS'] = df['Mapping_BS'].apply(lambda x: None if str(x).upper().strip() in ['NA', 'N/A', 'NAN', ''] else x)

            mappings[entite] = df
            print(f"  {entite} : {len(df)} comptes chargés")

        except Exception as e:
            print(f"  {entite} : onglet non trouvé ou erreur — {e}")

    return mappings


def appliquer_mapping(df_comptes, mappings):
    """
    Applique le mapping PCG aux mouvements par compte
    Génère une alerte pour les comptes non mappés

    Args:
        df_comptes : DataFrame agrégé par compte (sortie de 02)
        mappings   : dictionnaire de mappings par entité (sortie de load_mapping_pcg)

    Returns:
        df_mapped  : DataFrame avec les lignes P&L et BS
        df_alertes : DataFrame des comptes non mappés
    """

    dfs_mapped = []
    dfs_alertes = []

    for entite, df_mapping in mappings.items():

        # Filtre les mouvements de cette entité
        df_entite = df_comptes[df_comptes['Entite'] == entite].copy()

        if df_entite.empty:
            continue

        # Jointure avec le mapping
        df_merged = df_entite.merge(
            df_mapping[['CompteNum', 'Mapping_PL', 'Mapping_BS']],
            on='CompteNum',
            how='left'
        )

        # Détection des comptes non mappés
        # Un compte est non mappé uniquement si PL ET BS sont tous les deux vides
        non_mappes = df_merged[df_merged['Mapping_PL'].isna() & df_merged['Mapping_BS'].isna()]

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
    """
    Agrège les mouvements par ligne de P&L

    Args:
        df_mapped : DataFrame avec mapping appliqué

    Returns:
        DataFrame P&L agrégé par ligne et entité
    """

    # Filtre les comptes P&L (classe 6 et 7)
    df_pl = df_mapped[
        df_mapped['ClasseCompte'].isin(['6', '7']) &
        df_mapped['Mapping_PL'].notna()
    ].copy()

    # Agrégation par ligne P&L et entité
    pl = df_pl.groupby(
        ['Entite', 'Mapping_PL'],
        as_index=False
    ).agg(
        Mouvement=('Mouvement', 'sum')
    )

    # Inversion du signe pour les produits (classe 7)
    # En comptabilité les produits sont créditeurs donc négatifs
    # On les repasse en positif pour l'affichage P&L
    pl['Mouvement'] = pl['Mouvement'] * -1

    print(f"\nP&L agrégé : {pl['Mapping_PL'].nunique()} lignes distinctes")

    return pl


def agreger_bilan(df_soldes_bilan, mappings):
    """
    Agrège les soldes par ligne de bilan

    Args:
        df_soldes_bilan : DataFrame soldes bilan (sortie de 02)
        mappings        : dictionnaire de mappings par entité

    Returns:
        DataFrame Bilan agrégé par ligne et entité
    """

    dfs = []

    for entite, df_mapping in mappings.items():

        df_entite = df_soldes_bilan[df_soldes_bilan['Entite'] == entite].copy()

        if df_entite.empty:
            continue

        df_merged = df_entite.merge(
            df_mapping[['CompteNum', 'Mapping_BS']],
            on='CompteNum',
            how='left'
        )

        dfs.append(df_merged)

    df_merged_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    # Agrégation par ligne bilan et entité
    bilan = df_merged_all[df_merged_all['Mapping_BS'].notna()].groupby(
        ['Entite', 'Mapping_BS'],
        as_index=False
    ).agg(
        Solde=('Solde', 'sum')
    )

    print(f"Bilan agrégé : {bilan['Mapping_BS'].nunique()} lignes distinctes")

    return bilan


# Test du script
if __name__ == "__main__":

    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import (
        get_mouvements_mois,
        get_mouvements_par_compte,
        get_soldes_bilan
    )

    INPUT_FOLDER  = "data/fec"
    MAPPING_FOLDER = "mapping"

    # Chargement FEC
    PERIODE = detect_periode(INPUT_FOLDER)
    df      = load_fec_entites(INPUT_FOLDER, PERIODE)

    # Mouvements du mois
    df_mois    = get_mouvements_mois(df, PERIODE)
    df_comptes = get_mouvements_par_compte(df_mois)
    df_bilan   = get_soldes_bilan(df, PERIODE)

    # Chargement mapping
    mappings = load_mapping_pcg(MAPPING_FOLDER)

    # Application du mapping
    df_mapped, df_alertes = appliquer_mapping(df_comptes, mappings)

    # P&L agrégé
    df_pl = agreger_pl(df_mapped)
    print("\nAperçu P&L :")
    print(df_pl.to_string(index=False))

    # Bilan agrégé
    df_bilan_mapped = agreger_bilan(df_bilan, mappings)
    print("\nAperçu Bilan :")
    print(df_bilan_mapped.to_string(index=False))
