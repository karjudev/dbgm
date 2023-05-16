import requests
from bs4 import BeautifulSoup

dictionary = []


'''
    Semplice script per fare scraping dal sito brocardi.it.
'''
for i in range(1, 74):

    # Recupero la pagina HTML i dal sito 
    response = requests.get(f"https://www.brocardi.it/dizionario/?page={i}")

    # Utilizzo BeautifulSoup per convertire la pagina in HTML in un oggetto facilmente manovrabile
    soup = BeautifulSoup(response.text, 'html.parser')

    # Cerco la lista dei termini in base al tag <ul> e alla classe che li racchiude 'terms-list'
    terms_list = soup.findAll('ul', attrs={"class":"terms-list"})

    # Creo un ulteriore oggetto per parsare questo risultato
    soup2 = BeautifulSoup(str(terms_list), 'html.parser')

    # Cerco tutte le referenze a tag HTML <a>
    terms_list2 = soup2.findAll("a", text=True)

    # Appendo al dizionario ogni definizione 
    for element in terms_list2:
        dictionary.append(element.get_text())

# Scrivo tutto il dizionario su un file
with open("output.txt", "w") as txt_file:
    for line in dictionary:
        txt_file.write(line + "\n") 