import pandas as pd
import os
import re


def load_fec(filepath, nom_entite):
    """
    Charge et nettoie un FEC Quadra/Cegid

    Args:
        filepath   : chemin vers le fichier FEC
        nom_entite : nom de l'entité (ex: 'FR', 'PID', 'CELSIUS', 'VERTICAL')

    Returns:
        DataFrame pandas nettoyé
    """

    # Lecture du FEC
    df = pd.read_csv(
        filepath,
        sep='\t',
        encoding='utf-8',
        dtype=str
    )

    # Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip()

    # Conversion des dates (format AAAAMMJJ → date Python)
    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'], format='%Y%m%d')
    df['PieceDate']    = pd.to_datetime(df['PieceDate'],    format='%Y%m%d')

    # Conversion des montants (virgule → point pour Python)
    df['Debit']  = df['Debit'].str.replace(',', '.').astype(float)
    df['Credit'] = df['Credit'].str.replace(',', '.').astype(float)

    # Calcul du mouvement net
    df['Mouvement'] = df['Debit'] - df['Credit']

    # Nettoyage des colonnes texte
    for col in ['CompteNum', 'CompteLib', 'JournalCode']:
        df[col] = df[col].str.strip()

    # Gestion des colonnes auxiliaires parfois vides
    df['CompAuxNum'] = df['CompAuxNum'].fillna('').str.strip()
    df['CompAuxLib'] = df['CompAuxLib'].fillna('').str.strip()

    # Identification de l'entité
    df['Entite'] = nom_entite

    print(f"  {nom_entite} : {len(df)} lignes chargées")

    return df


def detect_fec_files(input_folder, periode):
    """
    Détecte automatiquement les fichiers FEC dans le dossier input
    pour une période donnée

    Args:
        input_folder : chemin vers data/input/
        periode      : période au format YYYYMM (ex: '202401')

    Returns:
        Dictionnaire {nom_entite: filepath}
    """

    entites_valides = ['FR', 'PID', 'CELSIUS', 'VERTICAL']
    entites_trouvees = {}

    for fichier in os.listdir(input_folder):
        # Pattern attendu : FEC_YYYYMM_ENTITE.txt
        pattern = rf'^FEC_{periode}_(\w+)\.txt$'
        match = re.match(pattern, fichier)

        if match:
            nom_entite = match.group(1).upper()
            if nom_entite in entites_valides:
                entites_trouvees[nom_entite] = os.path.join(input_folder, fichier)
                print(f"  Fichier détecté : {fichier} → Entité {nom_entite}")
            else:
                print(f"  Attention : entité inconnue dans {fichier} — ignoré")

    if not entites_trouvees:
        raise FileNotFoundError(
            f"Aucun fichier FEC trouvé pour la période {periode} dans {input_folder}"
        )

    return entites_trouvees


def detect_periode(input_folder):
    """
    Détecte automatiquement la période la plus récente
    dans le dossier input

    Args:
        input_folder : chemin vers data/input/

    Returns:
        Période au format YYYYMM
    """

    periodes = set()

    for fichier in os.listdir(input_folder):
        pattern = r'^FEC_(\d{6})_\w+\.txt$'
        match = re.match(pattern, fichier)
        if match:
            periodes.add(match.group(1))

    if not periodes:
        raise FileNotFoundError(f"Aucun fichier FEC trouvé dans {input_folder}")

    # Prend la période la plus récente
    periode = sorted(periodes)[-1]
    print(f"Période détectée automatiquement : {periode}")
    return periode


def load_fec_entites(input_folder, periode):
    """
    Charge et consolide les FEC de toutes les entités détectées
    pour une période donnée

    Args:
        input_folder : chemin vers data/input/
        periode      : période au format YYYYMM (ex: '202401')

    Returns:
        DataFrame consolidé toutes entités
    """

    print(f"\nChargement des FEC pour la période {periode}...")

    # Détection automatique des fichiers
    entites = detect_fec_files(input_folder, periode)

    # Chargement de chaque entité
    dfs = []
    for nom_entite, filepath in entites.items():
        df = load_fec(filepath, nom_entite)
        dfs.append(df)

    # Consolidation
    df_consolide = pd.concat(dfs, ignore_index=True)

    print(f"\nConsolidation terminée :")
    print(f"  Entités chargées  : {list(df_consolide['Entite'].unique())}")
    print(f"  Total lignes      : {len(df_consolide)}")
    print(f"  Période couverte  : {df_consolide['EcritureDate'].min().strftime('%d/%m/%Y')} → {df_consolide['EcritureDate'].max().strftime('%d/%m/%Y')}")
    print(f"  Comptes distincts : {df_consolide['CompteNum'].nunique()}")

    return df_consolide


# Test du script
if __name__ == "__main__":

    INPUT_FOLDER = "data/input"

    # Détection automatique de la période
    PERIODE = detect_periode(INPUT_FOLDER)

    df = load_fec_entites(INPUT_FOLDER, PERIODE)

    print("\nAperçu des données :")
    print(df.head())