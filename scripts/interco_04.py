import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_interco(mapping_folder):
    """
    Charge le fichier de configuration des intercos

    Args:
        mapping_folder : chemin vers le dossier mapping/

    Returns:
        df_interco_pl : DataFrame des intercos P&L
        df_interco_bs : DataFrame des intercos Bilan
    """

    filepath = os.path.join(mapping_folder, 'interco.xlsx')

    df_interco_pl = pd.read_excel(filepath, sheet_name='interco_PL', dtype=str)
    df_interco_bs = pd.read_excel(filepath, sheet_name='interco_BS', dtype=str)

    for df in [df_interco_pl, df_interco_bs]:
        df.columns = df.columns.str.strip()
        for col in df.columns:
            df[col] = df[col].fillna('').str.strip()

    print(f"\nConfiguration intercos chargée :")
    print(f"  Intercos P&L : {len(df_interco_pl)} paires")
    print(f"  Intercos BS  : {len(df_interco_bs)} paires")

    return df_interco_pl, df_interco_bs


def montant_avec_filtre(df_fec, entite, compte, filtre_lib):
    """
    Calcule le montant net pour un compte donné,
    avec filtre optionnel sur EcritureLib (liste de mots-clés séparés par virgules)

    Args:
        df_fec    : DataFrame FEC complet
        entite    : nom de l'entité
        compte    : numéro de compte
        filtre_lib: string de mots-clés séparés par virgules (ex: 'PID,PLUG IN DIGITAL')
                    vide = pas de filtre

    Returns:
        montant net (float)
    """

    masque = (
        (df_fec['Entite']    == entite) &
        (df_fec['CompteNum'] == compte)
    )

    if filtre_lib:
        mots_cles = [m.strip().upper() for m in filtre_lib.split(',')]
        masque_lib = df_fec['EcritureLib'].str.upper().apply(
            lambda x: any(mot in str(x) for mot in mots_cles)
        )
        masque = masque & masque_lib

    return df_fec[masque]['Mouvement'].sum()


def eliminer_intercos_pl(df_fec_mois, df_mapped, df_interco_pl):
    """
    Élimine les intercos P&L en utilisant le FEC du mois pour calculer
    les montants avec filtre sur EcritureLib

    Args:
        df_fec_mois    : DataFrame FEC filtré sur le mois (sortie de 02)
        df_mapped      : DataFrame avec mapping appliqué (sortie de 03)
        df_interco_pl  : DataFrame config intercos P&L

    Returns:
        df_elimine : DataFrame avec mouvements interco mis à zéro
        df_recap   : Récapitulatif des éliminations
    """

    print(f"\nÉlimination intercos P&L...")

    df_elimine = df_mapped.copy()
    recaps = []

    for _, row in df_interco_pl.iterrows():

        compte_a   = row['Compte_Entite_A']
        entite_a   = row['Entite_A']
        filtre_a   = row['Filtre_EcritureLib_A']
        compte_b   = row['Compte_Entite_B']
        entite_b   = row['Entite_B']
        filtre_b   = row['Filtre_EcritureLib_B']
        desc       = row['Description']

        # Montants depuis le FEC du mois avec filtre
        montant_a = montant_avec_filtre(df_fec_mois, entite_a, compte_a, filtre_a)
        montant_b = montant_avec_filtre(df_fec_mois, entite_b, compte_b, filtre_b)

        if montant_a == 0 and montant_b == 0:
            print(f"  ℹ️  {desc} : aucun mouvement ce mois — ignoré")
            continue

        ecart = montant_a + montant_b

        if abs(ecart) > 0.01:
            print(f"  ⚠️  {desc} : écart de {ecart:,.2f} — élimination forcée")
        else:
            print(f"  ✅ {desc} : élimination équilibrée ({montant_a:,.2f})")

        # Élimination dans df_mapped — on met à zéro les lignes concernées
        # avec le même filtre sur EcritureLib
        # Élimination dans df_mapped — pas de EcritureLib ici
        # On met à zéro tout le compte car df_mapped est déjà agrégé par compte
        # Le filtre EcritureLib a déjà servi à calculer les bons montants via df_fec_mois
        masque_a = (
            (df_elimine['Entite']    == entite_a) &
            (df_elimine['CompteNum'] == compte_a)
        )
        masque_b = (
            (df_elimine['Entite']    == entite_b) &
            (df_elimine['CompteNum'] == compte_b)
        )

        df_elimine.loc[masque_a, 'Mouvement'] = 0
        df_elimine.loc[masque_b, 'Mouvement'] = 0

        recaps.append({
            'Description' : desc,
            'Entite_A'    : entite_a,
            'Compte_A'    : compte_a,
            'Montant_A'   : montant_a,
            'Entite_B'    : entite_b,
            'Compte_B'    : compte_b,
            'Montant_B'   : montant_b,
            'Ecart'       : ecart
        })

    df_recap = pd.DataFrame(recaps)
    return df_elimine, df_recap


def solde_avec_filtre(df_bilan, entite, compte, filtre_lib):
    """
    Calcule le solde pour un compte donné,
    avec filtre optionnel sur EcritureLib

    Args:
        df_bilan   : DataFrame bilan avec comptes détaillés
        entite     : nom de l'entité
        compte     : numéro de compte
        filtre_lib : string de mots-clés séparés par virgules
                     vide = pas de filtre

    Returns:
        solde (float)
    """

    masque = (
        (df_bilan['Entite']    == entite) &
        (df_bilan['CompteNum'] == compte)
    )

    if filtre_lib:
        mots_cles = [m.strip().upper() for m in filtre_lib.split(',')]
        masque_lib = df_bilan['EcritureLib'].str.upper().apply(
            lambda x: any(mot in str(x) for mot in mots_cles)
        )
        masque = masque & masque_lib

    return df_bilan[masque]['Mouvement'].sum()


def eliminer_intercos_bs(df_fec_ytd, df_bilan_mapped, df_interco_bs):
    """
    Élimine les intercos du bilan.
    Utilise le FEC YTD pour calculer les soldes avec filtre EcritureLib.
    En cas d'écart, élimination forcée des deux côtés avec alerte.

    Args:
        df_fec_ytd     : DataFrame FEC complet YTD (pour filtrer par EcritureLib)
        df_bilan_mapped: DataFrame bilan agrégé avec mapping (sortie de 03)
        df_interco_bs  : DataFrame config intercos BS

    Returns:
        df_elimine : DataFrame bilan après élimination
        df_recap   : Récapitulatif des éliminations
    """

    print(f"\nÉlimination intercos Bilan...")

    df_elimine = df_fec_ytd.copy()
    recaps     = []

    # On a besoin du FEC YTD filtré jusqu'à fin du mois
    # avec EcritureLib pour les filtres
    df_fec_bs = df_fec_ytd.copy()

    for _, row in df_interco_bs.iterrows():

        compte_a = row['Compte_Entite_A']
        entite_a = row['Entite_A']
        filtre_a = row['Filtre_EcritureLib_A']
        compte_b = row['Compte_Entite_B']
        entite_b = row['Entite_B']
        filtre_b = row['Filtre_EcritureLib_B']
        desc     = row['Description']

        # Soldes depuis le FEC YTD avec filtre
        solde_a = solde_avec_filtre(df_fec_bs, entite_a, compte_a, filtre_a)
        solde_b = solde_avec_filtre(df_fec_bs, entite_b, compte_b, filtre_b)

        if solde_a == 0 and solde_b == 0:
            print(f"  ℹ️  {desc} : aucun solde — ignoré")
            continue

        ecart = solde_a + solde_b

        if abs(ecart) > 0.01:
            print(f"  ⚠️  {desc} : écart de {ecart:,.2f} — élimination forcée")
        else:
            print(f"  ✅ {desc} : élimination équilibrée ({solde_a:,.2f})")

        # Mise à zéro des mouvements dans le FEC YTD
        df_elimine.loc[
            (df_elimine['Entite']    == entite_a) &
            (df_elimine['CompteNum'] == compte_a),
            'Mouvement'
        ] = 0

        df_elimine.loc[
            (df_elimine['Entite']    == entite_b) &
            (df_elimine['CompteNum'] == compte_b),
            'Mouvement'
        ] = 0

        recaps.append({
            'Description' : desc,
            'Entite_A'    : entite_a,
            'Compte_A'    : compte_a,
            'Solde_A'     : solde_a,
            'Entite_B'    : entite_b,
            'Compte_B'    : compte_b,
            'Solde_B'     : solde_b,
            'Ecart'       : ecart
        })

    df_recap = pd.DataFrame(recaps)
    return df_elimine, df_recap


# Test du script
if __name__ == "__main__":

    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import (
        get_mouvements_mois,
        get_mouvements_par_compte,
        get_soldes_bilan
    )
    from scripts.pcg_mapping_03 import (
        load_mapping_pcg,
        appliquer_mapping,
        agreger_pl,
        agreger_bilan
    )

    INPUT_FOLDER   = "data/fec"
    MAPPING_FOLDER = "mapping"

    # Chargement FEC
    PERIODE    = detect_periode(INPUT_FOLDER)
    df         = load_fec_entites(INPUT_FOLDER, PERIODE)

    # Mouvements du mois
    df_mois    = get_mouvements_mois(df, PERIODE)
    df_comptes = get_mouvements_par_compte(df_mois)
    df_bilan   = get_soldes_bilan(df, PERIODE)

    # Mapping PCG
    mappings         = load_mapping_pcg(MAPPING_FOLDER)
    df_mapped, _     = appliquer_mapping(df_comptes, mappings)
    df_bilan_mapped  = agreger_bilan(df_bilan, mappings)

    # Chargement config intercos
    df_interco_pl, df_interco_bs = load_interco(MAPPING_FOLDER)

    # Élimination intercos P&L
    df_pl_elimine, recap_pl = eliminer_intercos_pl(df_mois, df_mapped, df_interco_pl)
    print("\nRécapitulatif éliminations P&L :")
    print(recap_pl.to_string(index=False))

    # Ré-agrégation P&L après élimination
    df_pl_final = agreger_pl(df_pl_elimine)
    print("\nP&L après éliminations intercos :")
    print(df_pl_final.to_string(index=False))

    # Élimination intercos Bilan
    df_bilan_elimine, recap_bs = eliminer_intercos_bs(df, df_bilan, df_interco_bs)
    print("\nRécapitulatif éliminations Bilan :")
    print(recap_bs.to_string(index=False))
