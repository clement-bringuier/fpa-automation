import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SEUIL_ECART_INTERCO


def load_interco(mapping_folder):
    filepath      = os.path.join(mapping_folder, 'interco.xlsx')
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


def _extraire_montant(df, entite, compte, filtre_lib):
    """Extrait le montant net (Mouvement) pour un compte/entité avec filtre optionnel."""
    masque = (df['Entite'] == entite) & (df['CompteNum'] == compte)

    if filtre_lib:
        mots = [m.strip().upper() for m in filtre_lib.split(',')]
        masque &= df['EcritureLib'].str.upper().apply(lambda x: any(m in str(x) for m in mots))

    return df[masque]['Mouvement'].sum()


def _log_elimination(desc, ecart, montant_ref, comment=''):
    if abs(ecart) > SEUIL_ECART_INTERCO:
        msg = f"  ⚠️  {desc} : écart de {ecart:,.2f} — élimination forcée"
        if comment:
            msg += f" ({comment})"
        print(msg)
    else:
        print(f"  ✅ {desc} : élimination équilibrée ({montant_ref:,.2f})")


def eliminer_intercos_pl(df_fec_mois, df_mapped, df_interco_pl):
    print(f"\nÉlimination intercos P&L...")

    df_elimine = df_mapped.copy()
    recaps     = []

    for _, row in df_interco_pl.iterrows():
        entite_a, compte_a, filtre_a = row['Entite_A'], row['Compte_Entite_A'], row['Filtre_EcritureLib_A']
        entite_b, compte_b, filtre_b = row['Entite_B'], row['Compte_Entite_B'], row['Filtre_EcritureLib_B']
        desc, comment = row['Description'], row.get('Commentaire', '')

        montant_a = _extraire_montant(df_fec_mois, entite_a, compte_a, filtre_a)
        montant_b = _extraire_montant(df_fec_mois, entite_b, compte_b, filtre_b)

        if montant_a == 0 and montant_b == 0:
            print(f"  ℹ️  {desc} : aucun mouvement ce mois — ignoré")
            continue

        ecart = montant_a + montant_b
        _log_elimination(desc, ecart, montant_a, comment)

        df_elimine.loc[(df_elimine['Entite'] == entite_a) & (df_elimine['CompteNum'] == compte_a), 'Mouvement'] = 0
        df_elimine.loc[(df_elimine['Entite'] == entite_b) & (df_elimine['CompteNum'] == compte_b), 'Mouvement'] = 0

        recaps.append({
            'Description': desc, 'Entite_A': entite_a, 'Compte_A': compte_a,
            'Montant_A': montant_a, 'Entite_B': entite_b, 'Compte_B': compte_b,
            'Montant_B': montant_b, 'Ecart': ecart, 'Commentaire': comment
        })

    return df_elimine, pd.DataFrame(recaps)


def eliminer_intercos_bs(df_fec_ytd, df_bilan_mapped, df_interco_bs):
    print(f"\nÉlimination intercos Bilan...")

    df_elimine = df_fec_ytd.copy()
    recaps     = []

    for _, row in df_interco_bs.iterrows():
        entite_a, compte_a, filtre_a = row['Entite_A'], row['Compte_Entite_A'], row['Filtre_EcritureLib_A']
        entite_b, compte_b, filtre_b = row['Entite_B'], row['Compte_Entite_B'], row['Filtre_EcritureLib_B']
        desc, comment = row['Description'], row.get('Commentaire', '')

        solde_a = _extraire_montant(df_fec_ytd, entite_a, compte_a, filtre_a)
        solde_b = _extraire_montant(df_fec_ytd, entite_b, compte_b, filtre_b)

        if solde_a == 0 and solde_b == 0:
            print(f"  ℹ️  {desc} : aucun solde — ignoré")
            continue

        ecart = solde_a + solde_b
        _log_elimination(desc, ecart, solde_a, comment)

        df_elimine.loc[(df_elimine['Entite'] == entite_a) & (df_elimine['CompteNum'] == compte_a), 'Mouvement'] = 0
        df_elimine.loc[(df_elimine['Entite'] == entite_b) & (df_elimine['CompteNum'] == compte_b), 'Mouvement'] = 0

        recaps.append({
            'Description': desc, 'Entite_A': entite_a, 'Compte_A': compte_a,
            'Solde_A': solde_a, 'Entite_B': entite_b, 'Compte_B': compte_b,
            'Solde_B': solde_b, 'Ecart': ecart, 'Commentaire': comment
        })

    return df_elimine, pd.DataFrame(recaps)


if __name__ == "__main__":
    from config import FOLDERS
    from scripts.load_fec_01 import load_fec_entites, detect_periode
    from scripts.monthly_movements_02 import get_mouvements_mois, get_mouvements_par_compte, get_soldes_bilan
    from scripts.pcg_mapping_03 import load_mapping_pcg, appliquer_mapping, agreger_pl, agreger_bilan

    periode          = detect_periode(FOLDERS["fec"])
    df               = load_fec_entites(FOLDERS["fec"], periode)
    df_mois          = get_mouvements_mois(df, periode)
    df_comptes       = get_mouvements_par_compte(df_mois)
    df_bilan         = get_soldes_bilan(df, periode)
    mappings         = load_mapping_pcg(FOLDERS["mapping"])
    df_mapped, _     = appliquer_mapping(df_comptes, mappings)
    df_bilan_mapped  = agreger_bilan(df_bilan, mappings)

    df_interco_pl, df_interco_bs = load_interco(FOLDERS["mapping"])

    df_pl_elimine, recap_pl = eliminer_intercos_pl(df_mois, df_mapped, df_interco_pl)
    print("\nRécapitulatif éliminations P&L :")
    print(recap_pl.to_string(index=False))

    df_pl_final = agreger_pl(df_pl_elimine)
    print("\nP&L après éliminations intercos :")
    print(df_pl_final.to_string(index=False))

    _, recap_bs = eliminer_intercos_bs(df, df_bilan_mapped, df_interco_bs)
    print("\nRécapitulatif éliminations Bilan :")
    print(recap_bs.to_string(index=False))