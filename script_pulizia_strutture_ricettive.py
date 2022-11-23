import pandas as pd

"""
Funzione che si occupa di settare in maiuscolo la prima lettera di ogni parola,
e di rimuovere la stringa "Citta' Metropolitana Di " quando precede il nome della città
"""
def capitalizeAndCleanValue(value):
    value = value.split(" ")
    temp = ""
    for ele in value:
        temp += ele.capitalize() + " "
    return temp.replace("Citta' Metropolitana Di ", "").strip()

df = pd.read_csv("Regione-Sicilia---Mappa-delle-strutture-ricettive.csv", sep = ";")

#Cancelliamo le seguenti colonne poiché saranno inutilizzate
df = df.drop(['Regione'], axis = 1)
df = df.drop(['Località'], axis = 1)
df = df.drop(['Sigla provincia'], axis = 1)

#Rinominiamo la colonna
df.rename(columns={'Indirizzo posta elettronica':'Email'}, inplace = True)

for index,row in df.iterrows():
    df.at[index,'Comune'] = capitalizeAndCleanValue(row["Comune"])
    df.at[index,'Provincia'] = capitalizeAndCleanValue(row["Provincia"])
    df.at[index,'Nome'] = row["Nome"].replace("\"", "")
      
df.to_csv("strutture_ricettive_pulito.csv", sep = ";", index=False)
