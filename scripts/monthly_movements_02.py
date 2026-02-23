import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CLASSES_BILAN, JOURNAL_AN


def get_mois_periode(periode):
    date_debut = pd.to_datetime(periode, format='%Y%m')
    date_fin   = date_debut + pd.offsets.MonthEnd(0)
    return date_debut, date_fin


def get_mouvements_mois(df, periode):
    date_debut, date_fin = get_mois_periode(periode)

    print(f"\nExtraction P&L — mouvements du mois {periode}")
    print(f"  Fenêtre : {date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")

    df_mois = df[
        (df['EcritureDate'] >= date_debut) &
        (df['EcritureDate'] <= date_fin)  &
        (df['JournalCode']  != JOURNAL_AN)
    ].copy()

    print(f"  Lignes extraites  : {len(df_mois)}")
    print(f"  Entités présentes : {list(df_mois['Entite'].unique())}")
    return df_mois


def get_soldes_bilan(df, periode):
    _, date_fin = get_mois_periode(periode)

    print(f"\nExtraction Bilan — soldes cumulés au {date_fin.strftime('%d/%m/%Y')}")

    df_ytd = df[df['EcritureDate'] <= date_fin].copy()

    soldes = df_ytd.groupby(
        ['Entite', 'CompteNum', 'CompteLib'], as_index=False
    ).agg(Solde=('Mouvement', 'sum'))

    soldes['ClasseCompte'] = soldes['CompteNum'].str[0]
    soldes_bilan = soldes[soldes['ClasseCompte'].isin(CLASSES_BILAN)].copy()

    print(f"  Lignes YTD    : {len(df_ytd)}")
    print(f"  Comptes bilan : {len(soldes_bilan)}")
    return soldes_bilan


def get_mouvements_par_compte(df_mois):
    mouvements = df_mois.groupby(
        ['Entite', 'CompteNum', 'CompteLib'], as_index=False
    ).agg(
        Debit     = ('Debit',     'sum'),
        Credit    = ('Credit',    'sum'),
        Mouvement = ('Mouvement', 'sum')
    )

    mouvements['ClasseCompte'] = mouvements['CompteNum'].str[0]
    mouvements = mouvements.sort_values(['Entite', 'CompteNum']).reset_index(drop=True)

    print(f"\nAgrégation par compte :")
    print(f"  Comptes distincts : {mouvements['CompteNum'].nunique()}")
    print(f"\nRépartition par classe :")
    for classe, grp in mouvements.groupby('ClasseCompte'):
        print(f"  Classe {classe} : {len(grp)} comptes — Mouvement net : {grp['Mouvement'].sum():,.2f}")

    return mouvements


if __name__ == "__main__":
    from config import FOLDERS
    from scripts.load_fec_01 import load_fec_entites, detect_periode

    periode    = detect_periode(FOLDERS["fec"])
    df         = load_fec_entites(FOLDERS["fec"], periode)
    df_mois    = get_mouvements_mois(df, periode)
    df_comptes = get_mouvements_par_compte(df_mois)
    df_bilan   = get_soldes_bilan(df, periode)

    print("\nAperçu mouvements P&L :")
    print(df_comptes.head(10))
    print("\nAperçu soldes Bilan :")
    print(df_bilan.head(10))