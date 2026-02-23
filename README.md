# FP&A Automation — Reporting Financier Consolidé IFRS

## Contexte
Automatisation complète du processus de clôture mensuelle pour un groupe de 4 entités :
- **FR** (Financière RANMA — Holding)
- **PID** (Plug In Digital — Publishing & Distribution)
- **CELSIUS** (Celsius Online — B2C & B2B)
- **VERTICAL** (Vertical — filiale)

## Problème résolu
Le processus manuel prenait 2 jours par mois impliquant :
- Consolidation manuelle de 4 FEC (format Quadra/Cegid)
- Éliminations des flux intercompagnies (management fees, FAE/FNP, comptes courants)
- Retraitements French GAAP → IFRS
- Split du CA et des COGS par Business Unit (Publishing / Distribution)
- Traitement de la masse salariale (split CAPEX/OPEX, répartition par BU)
- Isolation des CAPEX cash milestones

## Solution
Pipeline Python modulaire qui automatise l'intégralité du processus et génère :
- P&L consolidé par entité avec éliminations intercos
- P&L par Business Unit jusqu'à la contribution margin
- Bilan consolidé IFRS
- Free Cash-Flow consolidé (CAPEX milestones + CAPEX RH)

## Résultat
Réduction du temps de clôture de 3 jours à 10 minutes.

## Stack technique
- Python 3.11
- Pandas
- Openpyxl
- Git / GitHub

## Structure du projet
```
fpa-automation/
├── data/
│   ├── fec/              # Fichiers FEC par entité (non versionnés)
│   │                     # Format : FEC_YYYYMM_ENTITE.txt
│   ├── rh/               # Fichiers Silae + mapping RH (non versionnés)
│   │                     # Format : silae_YYYYMM_ENTITE.xlsx
│   └── revenue_cogs/     # Fichiers split CA/COGS par BU (non versionnés)
├── mapping/              # Fichiers de mapping (non versionnés)
│   ├── mapping_pcg.xlsx  # Mapping PCG par entité (onglets FR/PID/CELSIUS/VERTICAL)
│   └── interco.xlsx      # Configuration des éliminations intercos
├── scripts/
│   ├── load_fec_01.py           # Chargement et consolidation des FEC
│   ├── monthly_movements_02.py  # Extraction mouvements P&L et soldes bilan
│   ├── pcg_mapping_03.py        # Application du mapping PCG
│   ├── interco_04.py            # Éliminations intercompagnies
│   ├── bu_split_05.py           # Split CA/COGS/masse salariale par BU
│   ├── capex_07.py              # CAPEX cash milestones et CAPEX RH
│   └── output_09.py             # Génération des reportings Excel
├── main.py
└── requirements.txt
```

## Utilisation
1. Placer les FEC dans `data/fec/` au format `FEC_YYYYMM_ENTITE.txt`
2. Placer les fichiers Silae dans `data/rh/` au format `silae_YYYYMM_ENTITE.xlsx`
3. Mettre à jour `data/revenue_cogs/split_ca_cogs.xlsx` avec les données du mois
4. Lancer `python main.py`
5. Récupérer le reporting dans `data/output/`

## Notes
- Les écarts FAE/FNP intercos sont documentés dans `mapping/interco.xlsx` (colonne Commentaire)
- Le mapping RH (`data/rh/mapping_rh.xlsx`) doit être maintenu à jour pour les nouveaux salariés
- La détection de période est automatique (prend le FEC le plus récent dans `data/fec/`)