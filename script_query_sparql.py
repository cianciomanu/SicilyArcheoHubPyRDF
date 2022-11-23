from rdflib import Graph, URIRef, Literal, Namespace, RDF

g = Graph()
g.parse("dataset.ttl", format='turtle')

oso = Namespace("http://oursite.it/ontology/")
osr = Namespace("http://oursite.it/resource/")

g.bind("oso", oso)
g.bind("osr", osr)

def accomodation_facilities_per_province():
    #Con la seguente query otteniamo il numero di strutture ricettive per ogni provincia.
    results = g.query("""
        SELECT DISTINCT ?provinceName (COUNT(?accomodation) as ?nAccomodation)
        WHERE {
            ?accomodation oso:hasProvince ?province.
            ?province rdfs:label ?provinceName.
        }
        GROUP BY ?provinceName
        ORDER BY DESC(?nAccomodation)
    """)
    
    for row in results:
        print(row.provinceName + ";" + row.nAccomodation)
    
def total_ticket_cost_per_city():
    #Con la seguente query otteniamo il costo di tutti i biglietti interi per ogni città.
    #Quando il costo non è disponibile allora il sito archeologico non viene considerato
    results = g.query("""
        SELECT  ?cityName (SUM(?ticket_cost) as ?total_cost) (COUNT(?site)as ?nSite)
        WHERE {
            ?site oso:relatedCity ?city.
            ?city rdfs:label ?cityName.
            ?site oso:fullTicket ?ticket_cost
            FILTER(str(?ticket_cost) != 'Non Disponibile')
        }
        GROUP BY ?cityName
        ORDER BY ASC(?total_cost)
    """)
    
    for row in results:
        print(row.cityName + " ha " + row.nSite + " siti visitabili al costo totale di: " + row.total_cost)
        

def free_archaeological_sites_per_city():
    #Con la seguente query otteniamo una lista di siti archeologici con ingresso gratuito
    #indicando le relative città
    results = g.query("""
        SELECT ?city_label ?site_label
        WHERE {
            ?site oso:relatedCity ?city.
            ?city rdfs:label ?city_label.
            ?site rdfs:label ?site_label.
            ?site oso:fullTicket ?ticket_cost
            FILTER(?ticket_cost = 0.0)
        }
        ORDER BY (?city_label)

    """)
    
    for row in results:
        print(row.city_label + " - " + row.site_label)

def near_accomodation_site():
    #Con la seguente query otteniamo una lista di strutture ricettive e siti archeologici
    #che si trovano ad una distanza minore di 100 metri. 
    results = g.query("""
        SELECT ?city_name ?accomodation_name ?site_name ?distance
        WHERE {
            ?distanceB oso:distance ?distance;
                oso:relativeAccomodationFacility ?accomodation;
                oso:relativeArchaeologicalSite ?site.  
            ?accomodation rdfs:label ?accomodation_name;
                oso:relatedCity ?city.
            ?city rdfs:label ?city_name.
            ?site rdfs:label ?site_name
            FILTER (?distance < 100)
        }
        ORDER BY(?city_name)

    """)
    for row in results:
        print(row.city_name + " - " + row.accomodation_name + " <=> " + row.site_name + " with distance = " + row.distance)
        
        


def data_vis():
    #La seguente query ci permette di ottenere il numero di strutture ricettive dello stesso tipo per ogni provincia
    results = g.query("""
        SELECT DISTINCT ?provinceName (COUNT(?accomodation_type) as ?nAccomodation) ?accomodation_type
        WHERE {
            ?accomodation oso:facilityType ?accomodation_type.
            ?accomodation oso:hasProvince ?province.
            ?province rdfs:label ?provinceName                
        }
        GROUP BY ?accomodation_type ?provinceName 
        ORDER BY DESC(?accomodation_type)
    """)
    
    for row in results:
        print("Provincia: " + row.provinceName + " ha " + row.nAccomodation + " strutture ricettive di tipo " + row.accomodation_type)   
    results.serialize(destination="accomodation_n_per_province.csv", format="csv")
    
    
def query_esame():
    results = g.query("""
        SELECT ?archaeologicalSite
        WHERE {
            ?accomodation oso:hasProvince osr:Province_of_Palermo .
            ?accomodation oso:hasNearArchaeologicalSite ?distanceB .
            ?distanceB oso:relativeArchaeologicalSite ?archaeologicalSite
        }
    """)
    
    for row in results:
        print(row.archaeologicalSite)
    results.serialize(destination="accomodation_n_per_province.csv", format="csv")    
 


#accomodation_facilities_per_province()

#total_ticket_cost_per_city()

#free_archaeological_sites_per_city()

#near_accomodation_site()

query_esame()