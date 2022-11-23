from geopy import distance
import pandas as pd
from operator import itemgetter

from rdflib import Graph, Literal, Namespace, URIRef, XSD
from rdflib.namespace import RDF, RDFS, OWL

import urllib.parse #Utilizzata per URIficare le stringhe


g = Graph()
oso = Namespace("http://oursite.it/ontology/")
osr = Namespace("http://oursite.it/resource/")
dbo = Namespace("http://dbpedia.org/ontology/")
dbr = Namespace("http://dbpedia.org/resource/")
g.bind("osr", osr)
g.bind("dbo", dbo)
g.bind("dbr", dbr)
g.bind("oso", oso)

"""
Funzione che crea l'URI concatenando il nome del punto di interesse e 
del luogo in cui si trova, rimuovendo gli spazi
"""
def create_URI(denomination:str, place:str):
    return str(denomination.strip() + "-" + place.strip())

"""
Funzione che verifica l'esistenza di una città all'interno della base di conoscenza
DBpedia effettuando una query in Sparql
"""
def is_city(city_name:str): 
    uri = URIRef('http://dbpedia.org/resource/' + urllib.parse.quote(city_name.encode("UTF-8")))
    pp = URIRef('http://dbpedia.org/ontology/PopulatedPlace')

    g_temp = Graph()
    g_temp.parse(uri)
    response = g_temp.query(
        "ASK {?uri a ?pp}",
        initBindings={'uri': uri, 'pp': pp}
    )
    print(str(uri) + " is a PopulatedPlace? " + str(response.askAnswer))

    return response.askAnswer
    
"""
Funzione che verifica l'esistenza di una provincia all'interno della base di conoscenza
DBpedia effettuando una query in Sparql
"""
def is_province(province_name:str):
    province_name = "Province_of_" + province_name 
    uri = URIRef('http://dbpedia.org/resource/' +  urllib.parse.quote(province_name.encode("UTF-8")))
    prov = URIRef('http://dbpedia.org/resource/Provinces_of_Italy')

    g_temp = Graph()
    g_temp.parse(uri)
    g_temp.bind("dbo", dbo)
    response = g_temp.query(
        "ASK {?uri dbo:type ?prov}",
        initBindings={'uri': uri,'dbo':dbo,'prov': prov}
    )
    print(str(uri) + " is a Province? " + str(response.askAnswer))
    return response.askAnswer
    
    
#Prendiamo in input i file csv già puliti, utilizzando Pandas per la lettura
str_r = pd.read_csv("strutture_ricettive_pulito.csv", sep = ";")
sit_a = pd.read_csv("siti_archeologici_pulito.csv", sep = ";")

#Stringhe delle risorse delle basi di conoscenza utilizzate
base_r = "http://oursite.it/resource/"
base_r_dbpedia = "http://dbpedia.org/resource/"

#Trasposizione in RDF dei siti archeologici
for index, row in sit_a.iterrows():
    
    site_name = create_URI(row["Denominazione"], row["Comune"])
    site_name = urllib.parse.quote(site_name)
    
    #Per ogni riga del dataframe inseriamo nel grafo il sito archeologico con le sue proprietà
    poi = g.resource(base_r+site_name)
    poi.set(RDF.type,oso.ArchaeologicalSite)
    
    poi.set(oso.address, Literal(row["Indirizzo"], datatype=XSD.string))
    poi.set(oso.fullTicket, Literal(row["Ticket Intero"], datatype=XSD.float))
    poi.set(oso.reducedTicket, Literal(row["Ticket Ridotto"], datatype=XSD.float))
    poi.set(RDFS.label, Literal(row["Denominazione"], datatype=XSD.string))
    if(pd.notna(row["Nome Parco"])):
        poi.set(oso.parkName, Literal(row["Nome Parco"], datatype=XSD.string))
    if(pd.notna(row["Riferimenti Web"])):
        poi.set(oso.webReference, Literal(row["Riferimenti Web"], datatype=XSD.string))
    if(pd.notna(row["Cronologia"])):
        poi.set(oso.chronology, Literal(row["Cronologia"], datatype=XSD.string))
    poi.set(oso.siteType, Literal(row["Tipologia"], datatype=XSD.string))
    if(pd.notna(row["Info"])):
        poi.set(oso.info, Literal(row["Info"], datatype=XSD.string))
    if(pd.notna(row["Telefono"])):
        poi.set(oso.telephoneNumber, Literal(row["Telefono"], datatype=XSD.string))
    if(pd.notna(row["Email"])):
        poi.set(oso.email, Literal(row["Email"], datatype=XSD.string))
    if(pd.notna(row["Social"])):
        poi.set(oso.social, Literal(row["Social"], datatype=XSD.string))
    if(pd.notna(row["Orario"])):
        poi.set(oso.openingHours, Literal(row["Orario"], datatype=XSD.string))
        
    
    g.add((URIRef(base_r+site_name), oso.archaeologicalSheet, Literal(row["Sheet"], lang='en')))
    g.add((URIRef(base_r+site_name), oso.archaeologicalSheet, Literal(row["Scheda"], lang='it')))
    poi.set(oso.longitude, Literal(row["Long"], datatype=XSD.float))
    poi.set(oso.latitude, Literal(row["Lat"], datatype=XSD.float))
    poi.set(oso.image, Literal(row["Immagini"], datatype=XSD.string))
    if(pd.notna(row["Note"])):
        poi.set(oso.notes, Literal(row["Note"], datatype=XSD.string))
     
    #Creazione dell'entità City e collegamento con l'Archaeological Site 
    city_name = row["Comune"].replace(" ", "_")
    
    city_uri = URIRef(base_r + city_name)
    #Verifichiamo che la città non sia già all'interno del grafo, in questo creiamo l'entità con le sue proprietà
    if (URIRef(city_uri), RDF.type, oso.City) not in g:
        print("Controllando " + str(city_uri) + "...")
        city = g.resource(city_uri)
        city.set(RDF.type, oso.City)
        city.set(RDFS.label, Literal(row["Comune"], datatype=XSD.string))
        
        #Verifichiamo che la città sia presente su DBpedia
        if is_city(city_name):
            city.set(OWL.sameAs,URIRef(base_r_dbpedia+city_name))
        else:
            print("Nessun riferimento su DBpedia per la città: " + str(city_name))
        
    poi.set(oso.relatedCity, URIRef(city_uri))

sit_a = sit_a.reset_index(drop = True)
    
print("=> Fine Siti Archeologici\n\n")

#Trasposizione in RDF delle Province
for index , row in str_r.iterrows():
    province_name = row["Provincia"].replace(" ", "_")
    province_uri = URIRef(base_r +"Province_of_"+ province_name)
    if (province_uri, RDF.type, oso.Province) not in g:
        province = g.resource(province_uri)
        province.set(RDF.type, oso.Province)
        province.set(RDFS.label, Literal(row["Provincia"], datatype=XSD.string))
        
        if is_province(province_name):
            province.set(OWL.sameAs, URIRef(base_r_dbpedia+"Province_of_"+province_name))
        else:
            print("Nessun riferimento su DBpedia per la provincia: " + str(province_name))

str_r = str_r.reset_index(drop=True)
      
#Inseriamo manualmente interlinking per le province di Catania e Siracusa poiché su Dbpedia non sono
#segnate come Provinces_of_Italy
g.add((URIRef(base_r +"Province_of_Catania"), OWL.sameAs, URIRef(base_r_dbpedia+"Province_of_Catania")))       
g.add((URIRef(base_r +"Province_of_Siracusa"), OWL.sameAs, URIRef(base_r_dbpedia+"Province_of_Siracusa")))       

print("=> Fine Province")

#Trasposizione in RDF delle strutture ricettive
for index, row in str_r.iterrows():
    facility_name = create_URI(row["Nome"], row["Comune"])
    facility_name = urllib.parse.quote(facility_name)
    poi = g.resource(base_r+facility_name)
    poi.set(RDF.type,oso.AccomodationFacility)

    poi.set(oso.address, Literal(row["Indirizzo"], datatype=XSD.string))
    poi.set(oso.category, Literal(row["Categoria"], datatype=XSD.string))
    poi.set(oso.facilityType, Literal(row["Tipologia"],datatype=XSD.string))
    poi.set(RDFS.label, Literal(row["Nome"],datatype=XSD.string))
    if(pd.notna(row["Sito internet"])):
        poi.set(oso.website, Literal(row["Sito internet"], datatype=XSD.string))
    if(pd.notna(row["Telefono"])):
        poi.set(oso.telephoneNumber, Literal(row["Telefono"], datatype=XSD.string))
    if(pd.notna(row["Email"])):
        poi.set(oso.email, Literal(row["Email"], datatype=XSD.string))
    poi.set(oso.code, Literal(row["Codice"], datatype=XSD.string))
    poi.set(oso.longitude, Literal(row["Longitudine"], datatype=XSD.float))
    poi.set(oso.latitude, Literal(row["Latitudine"],datatype=XSD.float))
    
    #Creazione dell'entità City e collegamento con l'Accomodation Facility 
    city_name = row["Comune"].replace(" ", "_")
    
    city_uri = URIRef(base_r + city_name)
    if (URIRef(city_uri), RDF.type, oso.City) not in g:
        city = g.resource(city_uri)
        city.set(RDF.type, oso.City)
        city.set(RDFS.label, Literal(row["Comune"], datatype=XSD.string))
        
        if is_city(city_name):
            city.set(OWL.sameAs, URIRef(base_r_dbpedia+city_name))
        else:
            print("Nessun riferimento su DBpedia per la città: " + str(city_name))
            
    poi.set(oso.relatedCity, URIRef(city_uri))
    

    #Creazione dell'entità Province e collegamento con l'Accomodation Facility 
    province_name = row["Provincia"].replace(" ", "_")
    province_uri = URIRef(base_r+"Province_of_"+ province_name)
    if (URIRef(province_uri), RDF.type, oso.Province) in g:
        poi.set(oso.hasProvince, URIRef(province_uri))
        
str_r = str_r.reset_index(drop = True)  
print("=> Fine Strutture Ricettive\n\n")


#Creo arr_iter che contiene tuple con uri della struttura e latitudine e longitudine
arr_iter = []
for index, row in str_r.iterrows():
    facility_name = create_URI(row["Nome"], row["Comune"])
    facility_name = urllib.parse.quote(facility_name)
    facility_tuple = (facility_name,row["Latitudine"],row["Longitudine"])
    arr_iter.append(facility_tuple)
str_r = str_r.reset_index(drop = True)
#Creazione della risorsa DistanceBetween partendo dai siti archeologici, definendone le relazioni
for index,row in sit_a.iterrows():
    site_name = create_URI(row["Denominazione"], row["Comune"])
    site_name = urllib.parse.quote(site_name)

    site_coordinates = (row["Lat"],row["Long"])
    arr = [] #Array che contiene tutte le tuple che verranno successivamente ordinate in base alla distanza
    arr_final = [] #Array finale che contiene le tuple già ordinate da collegare
    for tuple in arr_iter:
        temp_coordinates = (tuple[1],tuple[2])
        dist = distance.distance(site_coordinates,temp_coordinates).m
        pair = (tuple[0], dist)
        arr.append(pair)
    arr = sorted(arr, key=itemgetter(1))
   
    #Prendiamo tutti gli hotel che sono entro i 500 metri,
    #se non raggiungiamo i 10 hotel, allora li aggiungiamo fino ad averne 10
    for ele in arr:
        if ele[1] < 500:
            arr_final.append(ele)
        elif len(arr_final) < 10:
            arr_final.append(ele)
        else: break

    for ele in arr_final:
        facility_name = ele[0]
        dist = ele[1]
        
        #Aggiungiamo al grafo la risorsa DistanceBetween
        betw = g.resource(base_r+site_name+facility_name)
        betw.set(RDF.type,oso.DistanceBetween)
        
        
        betw.set(oso.relativeArchaeologicalSite, URIRef(base_r+site_name))
        betw.set(oso.relativeAccomodationFacility, URIRef(base_r+facility_name))
        betw.set(oso.distance, Literal(dist, datatype = XSD.float))

        #Creiamo la tripla che collega il sito archeologico al singolo DistanceBetween
        g.add((URIRef(base_r+site_name), oso.hasNearAccomodationFacility, URIRef(base_r+site_name+facility_name)))

        facility = g.resource(base_r+facility_name)
        facility.set(oso.hasNearArchaeologicalSite, URIRef(base_r+site_name+facility_name))


sit_a = sit_a.reset_index(drop = True)  
  
print("=> Fine DistanceBetween Siti Archeologici\n\n")


#Creazione della risorsa DistanceBetween partendo dalle strutture ricettive, definendone le relazioni
arr_iter = []
for index, row in sit_a.iterrows():
    site_name = create_URI(row["Denominazione"], row["Comune"])
    site_name = urllib.parse.quote(site_name)
    site_tuple = (site_name,row["Lat"],row["Long"])
    arr_iter.append(site_tuple)
sit_a = sit_a.reset_index(drop = True)

for index,row in str_r.iterrows():
    facility_name = create_URI(row["Nome"], row["Comune"])
    facility_name = urllib.parse.quote(facility_name)
    
    facility_coordinates = (row["Latitudine"],row["Longitudine"])
    arr = []
    arr_final = []
    for tuple in arr_iter:
        temp_coord = (tuple[1],tuple[2])
        dist = distance.distance(facility_coordinates,temp_coord).m
        pair = (tuple[0], dist)
        arr.append(pair)
    arr = sorted(arr, key=itemgetter(1))
    
    #Prendiamo tutti i siti archeologici che sono entro i 500 metri,
    #se non raggiungiamo i 10 siti, allora li aggiungiamo fino ad averne 10
    for ele in arr:
        if ele[1] < 500:
            arr_final.append(ele)
        elif len(arr_final) < 10:
            arr_final.append(ele)
        else: break

    for ele in arr_final:
        site_name = ele[0]
        dist = ele[1]
        
        #Aggiugiamo al grafo la risorsa DistanceBetween se non è già stata creata in precedenza
        if (base_r+site_name+facility_name, RDF.type, oso.DistanceBetween) not in g:
            betw = g.resource(base_r+site_name+facility_name)
            betw.set(RDF.type,oso.DistanceBetween)
            
            
            betw.set(oso.relativeArchaeologicalSite, URIRef(base_r+site_name))
            betw.set(oso.relativeAccomodationFacility, URIRef(base_r+facility_name))
            betw.set(oso.distance, Literal(dist, datatype = XSD.float))

            #Creiamo la tripla che collega la struttura ricettiva al singolo DistanceBetween
            g.add((URIRef(base_r+facility_name), oso.hasNearArchaeologicalSite, URIRef(base_r+site_name+facility_name)))
            if (URIRef(base_r+site_name), oso.hasNearAccomodationFacility, URIRef(base_r+site_name+facility_name)) not in g:
                g.add((URIRef(base_r+site_name), oso.hasNearAccomodationFacility, URIRef(base_r+site_name+facility_name)))

        else:
            print("DistanceBetween già presente: " + base_r+site_name+facility_name)

    sit_a = sit_a.reset_index(drop = True)
print("=> Fine DistanceBetween Strutture Ricettive\n\n")

g.serialize(destination='dataset.ttl', format='turtle')

