import pandas as pd
df = pd.read_csv('data/fec/FEC_202512_PID.txt', sep='\t', dtype=str)
df['Credit'] = df['Credit'].str.replace(',', '.').astype(float)
df['Debit'] = df['Debit'].str.replace(',', '.').astype(float)

fournisseurs_0f = df[
    (df['CompteNum'].str.startswith('401')) &
    (df['CompAuxNum'].str.startswith('0F', na=False))
]
print(fournisseurs_0f[['EcritureDate','CompAuxNum','CompAuxLib','EcritureLib','Debit','Credit']].to_string())
print(f'Total credits (compta) : {fournisseurs_0f["Credit"].sum():,.2f}')
print(f'Total debits (paiements) : {fournisseurs_0f["Debit"].sum():,.2f}')