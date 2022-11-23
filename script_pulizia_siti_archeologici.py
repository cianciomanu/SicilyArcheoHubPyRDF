import pandas as pd
import re

"""
Funzioni per il parsing della stringa che contiene il simbolo '€' per
poi ottenere il valore numerico
"""
def _extract_price(value):
    match = re.match('^(.*?)([\d\.,]+)(.*)$', value)
    if match is None:
        raise ValueError("Non è possibile estrarre il valore = ", value)
    return match.groups()


def _parse_price(price, thousand, decimal):
    trans = str.maketrans(decimal, '.', thousand)
    return float(price.translate(trans))


def parse_price(value):
    prefix, price, suffix = _extract_price(value)
    if '€' in prefix + suffix:
        thousand = '.'
        decimal = ','
    else:
        thousand = ','
        decimal = '.'
    return _parse_price(price, thousand, decimal)

df = pd.read_csv("siti-archeologici_csv_rsd.csv", sep = ";")

#Cancelliamo le seguenti colonne poiché saranno inutilizzate
df = df.drop(['OBJECTID'], axis = 1)
df = df.drop(['CODISTAT'], axis = 1)
df = df.drop(['data_caricamento'], axis = 1)
df = df.drop(['Fax'], axis = 1)

#Rinominiamo le colonne
df.rename(columns={'X':'Long', 'Y':'Lat', 'denom':'Denominazione','Localiz':'Indirizzo',
                  'nomeparco': 'Nome Parco', 'weblink':'Riferimenti Web', 'cronologia':'Cronologia',
                  'info':'Info', 'Ticket_rid':'Ticket Ridotto', 'e_mail': 'Email', 'Ticket':'Ticket Intero',
                   'FotoImage': 'Immagini'}, inplace = True)

"""
Utilizzando la funzione di parsing di cui sopra, scorriamo tutte le righe e impostiamo a 0.0
quando il costo dei biglietto è Libero o Gratuito.
Se il prezzo non è specificato andremo ad indicare che è 'Non Disponibile'.
Questo avviene sia per Ticket Intero, che per Ticket Ridotto
"""
for index, row in df.iterrows():
    if row['Ticket Intero'] == "Gratuito":
        df.at[index, 'Ticket Intero'] = 0.0
    elif row['Ticket Intero'] == "Libero":
        df.at[index, 'Ticket Intero'] = 0.0
    elif pd.isna(row['Ticket Intero']):
        df.at[index, 'Ticket Intero'] = 'Non Disponibile'
    else:
        df.at[index, 'Ticket Intero'] = parse_price(str(row['Ticket Intero']))

        
df = df.reset_index(drop = True)

for index, row in df.iterrows():
    if row['Ticket Ridotto'] == "Gratuito":
        df.at[index, 'Ticket Ridotto'] = 0.0
    elif row['Ticket Ridotto'] == "Libero":
        df.at[index, 'Ticket Ridotto'] = 0.0
    elif pd.isna(row['Ticket Ridotto']):
        df.at[index, 'Ticket Ridotto'] = 'Non Disponibile'
    else:
        df.at[index, 'Ticket Ridotto'] = parse_price(str(row['Ticket Ridotto']))
        
df = df.reset_index(drop = True)

#Rendiamo minuscoli tutti i caretteri della Email
for index, row in df.iterrows():
    df.at[index, 'Email'] = str(df.at[index, 'Email']).lower()
df = df.reset_index(drop = True)

df.to_csv("siti_archeologici_pulito.csv", sep=';', encoding='utf-8', index = False)