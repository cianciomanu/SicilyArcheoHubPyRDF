from typing import Any
from telegram.ext import Updater
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import csv
from geopy import distance

import rdflib
from rdflib import Graph, URIRef, Literal, Namespace, RDF


g = Graph()
g.parse("dataset.ttl", format='turtle')

oso = Namespace("http://oursite.it/ontology/")
osr = Namespace("http://oursite.it/resource/")

g.bind("oso", oso)
g.bind("osr", osr)

def queryAccomodationFacilities():
    facilitiesList = []
    #Query su tutte le strutture ricettive
    facilities = g.query("""
        SELECT ?facility ?latitude ?longitude
        
        WHERE {
            ?facility a oso:AccomodationFacility .
            ?facility oso:latitude ?latitude .
            ?facility oso:longitude ?longitude
        }
    """)
        
    for row in facilities:
        tuple = (row.facility, row.latitude, row.longitude)
        facilitiesList.append(tuple)
        
    return facilitiesList


def find_accomodation_facility(facilityURI:str):
    results = g.query("""
        SELECT ?facilityLabel ?facilityLatitude ?facilityLongitude ?facilityType ?website ?facilityTelephoneNumber ?facilityEmail
        WHERE {
            """ + facilityURI + """ rdfs:label ?facilityLabel ;
                oso:latitude ?facilityLatitude ;
                oso:longitude ?facilityLongitude ;
                oso:facilityType ?facilityType .
            OPTIONAL { """ + facilityURI + """ oso:website ?website . }
            OPTIONAL { """ + facilityURI + """ oso:telephoneNumber ?facilityTelephoneNumber . }
            OPTIONAL { """ + facilityURI + """ oso:email ?facilityEmail . }
        }
    """)    
    return results

def find_Archaeological_site(facilityURI:str):
    results = g.query("""
        SELECT ?siteLabel ?siteImage ?archeoLatitude ?archeoLongitude ?fullTicket ?reducedTicket ?openingHours ?sheet
        WHERE {
            """ + facilityURI + """ oso:hasNearArchaeologicalSite ?distanceB .
            ?distanceB oso:relativeArchaeologicalSite ?archaeologicalSite .
            ?archaeologicalSite rdfs:label ?siteLabel ;
                oso:latitude ?archeoLatitude ;
                oso:longitude ?archeoLongitude ;
                oso:fullTicket ?fullTicket ;    
                oso:reducedTicket ?reducedTicket ;  
                oso:image ?siteImage;
                oso:archaeologicalSheet  ?sheet.
            OPTIONAL { ?archaeologicalSite oso:openingHours ?openingHours . }
            FILTER(LANG(?sheet) = 'it')    
                       
        }
    """)    
    
    return results


TOKEN = '' #insert token here

facilitiesList = queryAccomodationFacilities()
print("Abbiamo ottenuto la lista completa delle strutture ricettive.")

numero_hotel = 5

start_text = "Ciao!\nManda la tua posizione per iniziare ad utilizzare il bot"


updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher


# Comando /start
def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)


def location(update: Update, context: CallbackContext):
    # Ottengo la posizione dell'utente
    user_location = (update.message.location.latitude, update.message.location.longitude)
    print(user_location)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Sto cercando i " + str(numero_hotel) + " hotel più vicini a te")
    
    #Otteniamo i 3 hotel più vicini    
    distances_dictionary = {}
    for facility in facilitiesList:
        distances_dictionary[facility[0]] = distance.distance(user_location, (facility[1], facility[2])).m
    
    sorted_distances_dictionary = sorted(distances_dictionary.items(), key=lambda item: item[1])
    
    list_first_facilities_and_distances = list(sorted_distances_dictionary)[0:numero_hotel]
    
    #print(list_first_facilities_and_distances)
    
    nearest_facilities_uris = []
    for facility_distance_tuple in list_first_facilities_and_distances:
        nearest_facilities_uris.append(facility_distance_tuple[0])
    
    print("Stampo contenuto list_first_facilities_and_distances:\n")
    for ele in list_first_facilities_and_distances:
        print(ele[0] + " a distance = " + str(ele[1]))
    
    
    for uri in nearest_facilities_uris:
        res = find_accomodation_facility("<"+uri+">")
        for row in res:
            text_to_send = "----------------------------------------\n" + row.facilityLabel +" - "+ row.facilityType
            dist = distance.distance(user_location, (row.facilityLatitude, row.facilityLongitude)).m
            text_to_send += "\nDistanza: " + str(round(dist,2)) + " metri dalla tua posizione"
            if(row.website):
                text_to_send += str("\nSito Web: " + row.website)
            if(row.facilityTelephoneNumber):
                facili_n = "+39"+ row.facilityTelephoneNumber.replace(" ","")
                text_to_send += str("\nNumero di Telefono: " + facili_n)
            if(row.facilityEmail):
                text_to_send += str("\nEmail: " + row.facilityEmail)
            text_to_send += "\nCoordinate:"
            context.bot.send_message(chat_id=update.effective_chat.id,
                                            parse_mode="markdown",
                                            text=text_to_send)
            context.bot.sendLocation(chat_id=update.effective_chat.id, latitude=row.facilityLatitude,
                                            longitude=row.facilityLongitude)
            
    
    sities = []
    for uri in nearest_facilities_uris:
        res = find_Archaeological_site("<"+uri+">")  
        for ele in res:
            if ele not in sities:
                sities.append(ele)
    
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Ecco quali siti archeologici puoi visitare nelle tue vicinanze:") 
           
    for row in sities:
        dist = distance.distance(user_location, (row.archeoLatitude, row.archeoLongitude)).m
        text_to_send = "----------------------------------------\n" + row.siteLabel + "\nDistanza: " + str(round(dist,2)) + " metri dalla tua posizione"
        if(str(row.fullTicket) != 'Non Disponibile'):
            text_to_send += "\nTicket intero: " + str(row.fullTicket) + " €"
        elif str(row.fullTicket) != '0.0':
            text_to_send += "\nTicket intero: Ingresso gratuito" 
        else:
            text_to_send += "\nTicket Intero: " + str(row.fullTicket)
            
        if(str(row.fullTicket) != 'Non Disponibile'):
            text_to_send += "\nTicket ridotto: " + str(row.reducedTicket)+ " €"
        elif str(row.fullTicket) != '0.0':
            text_to_send += "\nTicket ridotto: Ingresso gratuito" 
        else:
            text_to_send += "\nTicket ridotto: " + str(row.reducedTicket)
        if(row.openingHours):
            text_to_send += "\nOrario di apertura: " + row.openingHours 
        text_to_send += "\n[Scheda approfondimenti]("+row.sheet+")"
        text_to_send += "\nA seguire troverai un'immagine del sito archeologico e le sue coordinate:" 
        context.bot.send_message(chat_id=update.effective_chat.id,
                                        parse_mode="markdown",
                                        text=text_to_send)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo = row.siteImage)
        
        
        context.bot.sendLocation(chat_id=update.effective_chat.id, latitude=row.archeoLatitude,
                                        longitude=row.archeoLongitude)
            


start_handler = CommandHandler('start', start)
location_handler = MessageHandler(Filters.location, location)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(location_handler)

updater.start_polling()

updater.idle()
