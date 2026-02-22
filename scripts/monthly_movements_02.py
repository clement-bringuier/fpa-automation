import pandas as pd


def get_mois_periode(periode):
    """
    Retourne le premier et dernier jour du mois
    à partir d'une période YYYYMM

    Args:
        periode : str au format YYYYMM (ex: '202601')

    Returns:
        date_debut, date_fin : dates de début et fin du mois
    """
    date_debut = pd.to_datetime(periode, format='%Y%m')
    date_fin   = date_debut + pd.offsets.MonthEnd(0)
    return date_debut, date_fin


def get_mouvements_mois(df, periode):
    """
    Extrait les mouvements du mois M pour le P&L
    Exclut les écritures A Nouveaux (JournalCode = 'AN')
    Filtre sur EcritureDate

    Args:
        df      : DataFrame FEC consolidé (sortie de 01_load_fec)
        periode : str au format YYYYMM (ex: '202601')

    Returns:
        DataFrame des mouvements du mois pour le P&L
    """

    date_debut, date_fin = get_mois_periode(periode)

    print(f"\nExtraction P&L — mouvements du mois {periode}")
    print(f"  Fenêtre : {date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")

    # Filtre sur la période
    masque_periode = (
        (df['EcritureDate'] >= date_debut) &
        (df['EcritureDate'] <= date_fin)
    )

    # Exclusion des A Nouveaux
    masque_an = df['JournalCode'] != 'AN'

    df_mois = df[masque_periode & masque_an].copy()

    print(f"  Lignes extraites  : {len(df_mois)}")
    print(f"  Entités présentes : {list(df_mois['Entite'].unique())}")

    return df_mois


def get_soldes_bilan(df, periode):
    """
    Calcule les soldes cumulés YTD pour le bilan
    Inclut les A Nouveaux
    Filtre toutes les écritures jusqu'à la fin du mois M

    Args:
        df      : DataFrame FEC consolidé (sortie de 01_load_fec)
        periode : str au format YYYYMM (ex: '202601')

    Returns:
        DataFrame des soldes par compte pour le bilan
    """

    date_debut, date_fin = get_mois_periode(periode)

    print(f"\nExtraction Bilan — soldes cumulés au {date_fin.strftime('%d/%m/%Y')}")

    # Filtre tout ce qui est <= fin du mois (AN inclus)
    df_ytd = df[df['EcritureDate'] <= date_fin].copy()

    # Calcul des soldes par compte et entité
    soldes = df_ytd.groupby(
        ['Entite', 'CompteNum', 'CompteLib'],
        as_index=False
    ).agg(
        Debit_Cumul  = ('Debit',     'sum'),
        Credit_Cumul = ('Credit',    'sum'),
        Solde        = ('Mouvement', 'sum')
    )

    # Ajout de la classe de compte (premier chiffre)
    soldes['ClasseCompte'] = soldes['CompteNum'].str[0]

    # Filtrage bilan : comptes de classe 1 à 5
    soldes_bilan = soldes[soldes['ClasseCompte'].isin(['1', '2', '3', '4', '5'])].copy()

    print(f"  Lignes YTD        : {len(df_ytd)}")
    print(f"  Comptes bilan     : {len(soldes_bilan)}")

    return soldes_bilan


def get_mouvements_par_compte(df_mois):
    """
    Agrège les mouvements du mois par compte et entité
    pour alimenter le P&L

    Args:
        df_mois : DataFrame mouvements du mois (sortie de get_mouvements_mois)

    Returns:
        DataFrame agrégé par compte
    """

    mouvements = df_mois.groupby(
        ['Entite', 'CompteNum', 'CompteLib'],
        as_index=False
    ).agg(
        Debit    = ('Debit',     'sum'),
        Credit   = ('Credit',   'sum'),
        Mouvement = ('Mouvement', 'sum')
    )

    # Ajout de la classe de compte
    mouvements['ClasseCompte'] = mouvements['CompteNum'].str[0]

    # Tri par entité et compte
    mouvements = mouvements.sort_values(['Entite', 'CompteNum']).reset_index(drop=True)

    print(f"\nAgrégation par compte :")
    print(f"  Comptes distincts : {mouvements['CompteNum'].nunique()}")
    print(f"\nRépartition par classe :")
    for classe, grp in mouvements.groupby('ClasseCompte'):
        print(f"  Classe {classe} : {len(grp)} comptes — Mouvement net : {grp['Mouvement'].sum():,.2f}")

    return mouvements


# Test du script
if __name__ == "__main__":

    # Import du script 01
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.load_fec_01 import load_fec_entites, detect_periode

    INPUT_FOLDER = "data/input"

    # Détection automatique de la période
    PERIODE = detect_periode(INPUT_FOLDER)

    # Chargement du FEC
    df = load_fec_entites(INPUT_FOLDER, PERIODE)

    # Mouvements du mois pour le P&L
    df_mois = get_mouvements_mois(df, PERIODE)

    # Agrégation par compte
    df_comptes = get_mouvements_par_compte(df_mois)

    # Soldes bilan
    df_bilan = get_soldes_bilan(df, PERIODE)

    print("\nAperçu mouvements P&L :")
    print(df_comptes.head(10))

    print("\nAperçu soldes Bilan :")
    print(df_bilan.head(10))