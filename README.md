# FP&A Automation — Reporting Financier Consolidé IFRS

## Contexte
Automatisation complète du processus de clôture mensuelle pour un groupe 
de 2 entités (Holding & Fililale)

## Problème résolu
Le processus manuel prenait 2 jours par mois impliquant :
- Consolidation manuelle de 2 FEC
- Retraitements French GAAP → IFRS
- Split du CA et des charges par Business Unit (Publishing / Distribution)
- Traitement de la masse salariale et activation R&D
- Isolation des CAPEX cash

## Solution
Script Python qui automatise l'intégralité du processus et génère 
automatiquement :
- P&L consolidé par Business Unit
- Bilan consolidé IFRS
- Free Cash-Flow consolidé

## Résultat
Réduction du temps de clôture de 2 jours à 10 minutes.

## Stack technique
- Python 3.11
- Pandas
- Openpyxl / XlsxWriter
- Git / GitHub

## Structure du projet
\```
fpa-automation/
├── data/
│   ├── input/          # Fichiers sources (non versionnés)
│   └── output/         # Reportings générés (non versionnés)
├── mapping/            # Fichiers de mapping (non versionnés)
├── scripts/
│   ├── 01_load_fec.py
│   ├── 02_monthly_movements.py
│   ├── 03_bu_split.py
│   ├── 04_payroll.py
│   ├── 05_capex.py
│   ├── 06_ifrs16.py
│   └── 07_output.py
├── main.py
└── requirements.txt
\```

## Utilisation
1. Placer les fichiers sources dans `data/input/`
2. Lancer `main.py`
3. Récupérer le reporting dans `data/output/`