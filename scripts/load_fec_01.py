import pandas as pd
import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ENTITES


def load_fec(filepath, nom_entite):
    df = pd.read_csv(filepath, sep='\t', encoding='utf-8', dtype=str)
    df.columns = df.columns.str.strip()

    df['EcritureDate'] = pd.to_datetime(df['EcritureDate'], format='%Y%m%d')
    df['Debit']        = df['Debit'].str.replace(',', '.').astype(float)
    df['Credit']       = df['Credit'].str.replace(',', '.').astype(float)
    df['Mouvement']    = df['Debit'] - df['Credit']

    for col in ['CompteNum', 'CompteLib', 'JournalCode']:
        df[col] = df[col].str.strip()

    df['CompAuxNum'] = df['CompAuxNum'].fillna('').str.strip()
    df['CompAuxLib'] = df['CompAuxLib'].fillna('').str.strip()
    df['Entite']     = nom_entite

    print(f"  {nom_entite} : {len(df)} lignes chargées")
    return df


def detect_fec_files(input_folder, periode):
    entites_trouvees = {}

    for fichier in os.listdir(input_folder):
        match = re.match(rf'^FEC_{periode}_(\w+)\.txt$', fichier)
        if match:
            nom_entite = match.group(1).upper()
            if nom_entite in ENTITES:
                entites_trouvees[nom_entite] = os.path.join(input_folder, fichier)
                print(f"  Fichier détecté : {fichier} → Entité {nom_entite}")
            else:
                print(f"  Attention : entité inconnue dans {fichier} — ignoré")

    if not entites_trouvees:
        raise FileNotFoundError(f"Aucun fichier FEC trouvé pour la période {periode} dans {input_folder}")

    return entites_trouvees


def detect_periode(input_folder):
    periodes = set()

    for fichier in os.listdir(input_folder):
        match = re.match(r'^FEC_(\d{6})_\w+\.txt$', fichier)
        if match:
            periodes.add(match.group(1))

    if not periodes:
        raise FileNotFoundError(f"Aucun fichier FEC trouvé dans {input_folder}")

    periode = sorted(periodes)[-1]
    print(f"Période détectée automatiquement : {periode}")
    return periode


def load_fec_entites(input_folder, periode):
    print(f"\nChargement des FEC pour la période {periode}...")

    entites = detect_fec_files(input_folder, periode)
    dfs     = [load_fec(fp, ent) for ent, fp in entites.items()]
    df      = pd.concat(dfs, ignore_index=True)

    print(f"\nConsolidation terminée :")
    print(f"  Entités chargées  : {list(df['Entite'].unique())}")
    print(f"  Total lignes      : {len(df)}")
    print(f"  Période couverte  : {df['EcritureDate'].min().strftime('%d/%m/%Y')} → {df['EcritureDate'].max().strftime('%d/%m/%Y')}")
    print(f"  Comptes distincts : {df['CompteNum'].nunique()}")

    return df


if __name__ == "__main__":
    from config import FOLDERS
    periode = detect_periode(FOLDERS["fec"])
    df      = load_fec_entites(FOLDERS["fec"], periode)
    print("\nAperçu des données :")
    print(df.head())