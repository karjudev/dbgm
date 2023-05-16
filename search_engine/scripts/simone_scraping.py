import requests
from bs4 import BeautifulSoup
import string


ALPHABET = list(string.ascii_lowercase)
BASE_URL = "https://dizionari.simone.it/idx/"

total_entries = []

for letter in ALPHABET:
    current_entries = []
    response = requests.get(f"{BASE_URL}{letter}")
    soup = BeautifulSoup(response.text, 'html.parser')
    terms_list_entries = soup.findAll("li", attrs={"class":"voce"})
    soup2 = BeautifulSoup(str(terms_list_entries), 'html.parser')
    terms_anchors = soup2.findAll("a", text=True)
    terms_dictionaries = soup2.findAll("span", attrs={"style": "font-weight:700; color:#666;"})
    for element, dictionary in zip(terms_anchors, terms_dictionaries):
        if dictionary.get_text().lower().strip() != "dizionario giuridico":
            continue
        current_entries.append(element.get_text())
    current_entries = list(set(current_entries))
    total_entries.extend(current_entries)


with open("raw_simone_juridic_dictionary.txt", "w", encoding="utf-8") as txt_file:
    for line in total_entries:
        txt_file.write(line + "\n")
