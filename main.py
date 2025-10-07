"""
main.py: Třetí projekt do Engeto Online Python Akademie

author: Jakub Miller
email: millerjakub17@gmail.com
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import Optional
import csv
from collections import Counter
import sys


session = requests.Session()

# Set TEST = True if you want to see error messages (mainly for URL responses)
TEST = True

def load_url(url: str, retries=6, delay=6, min_size=2000) -> Optional[BeautifulSoup]:
    """
    Load HTML from selected url.
    Returns BeautifulSoup object, or None if it doesn't connect.
    """
    for i in range(retries):
        try:
            response = session.get(url, timeout=10)
            if response.ok and len(response.content) > min_size:
                return BeautifulSoup(response.text, "html.parser")
            elif TEST: 
                if len(response.content) < min_size:
                    print(f"Suspiciously small response in bytes on {url}")
                else:
                    print(f"Error {response.status_code}, attempt {i+1}/{retries}")
        except requests.exceptions.RequestException as e:
            if TEST:
                print(f"Request failed: {e}, attempt {i+1}/{retries}")  

        # Increasing delay to give the web more time if it fails             
        time.sleep(min(delay * (2 ** i), 150))  
    return None


def get_all_precincts(url: str) -> list[dict]:
    """
    From the main page of district it obtains
    code, name and url of all precincts
    """
    soup = load_url(url)
    if soup is None:
        return []

    print(f"Stahuji data z vybraného URL: {url}")
    precinct_data = []
    rows = soup.find_all("tr")
    base_url = url.rsplit("/", 1)[0] + "/"
    for row in rows:
        cells = row.find_all("td")
        try:
            if len(cells) >= 3:
                code = cells[0].get_text(strip=True)
                name = cells[1].get_text(strip=True)
                if code.isdigit():
                    link_tag = cells[2].find("a")
                    if link_tag and "href" in link_tag.attrs:
                        link = base_url + link_tag["href"]
                        precinct_data.append({
                            "code": code,
                            "location": name,
                            "url": link
                        })
        except Exception as e:
            if TEST:
                print(f"Error at row: {row} - {e}")
    return precinct_data


def get_basic_stats(soup: BeautifulSoup) -> dict:
    """
    Extracts basic voting stats from the precinct page:
    - registered voters
    - envelopes issued
    - valid votes
    """
    result = {}
    mapping = {
        "sa2": "registered",
        "sa3": "envelopes",
        "sa6": "valid"
    }

    for header, key in mapping.items():
        cell = soup.find("td", headers=header)
        if cell:
            text = cell.get_text(strip=True).replace("\xa0", "")
            if text.isdigit():
                result[key] = int(text)

    return result


def get_party_votes(soup: BeautifulSoup) -> dict:
    """
    Extracts political party names and their vote counts
    from the second table on the precinct page.
    """
    result = {}
    rows = soup.find_all("tr")

    for row in rows:
        party_cell = row.find("td", class_="overflow_name")
        votes_cell = row.find("td", class_="cislo", headers=lambda h: h and "sa2" in h)
        if party_cell and votes_cell:
            party_name = party_cell.get_text(strip=True)
            votes_text = votes_cell.get_text(strip=True).replace("\xa0", "")
            if votes_text.isdigit():
                result[party_name] = int(votes_text)

    return result


def get_precinct_detail(soup: BeautifulSoup) -> Optional[dict]:
    """
    Combines both basic stats and party votes into one dictionary.
    """
    basic_stats = get_basic_stats(soup)
    party_votes = get_party_votes(soup)

    expected_keys = {"registered", "envelopes", "valid"}
    if not expected_keys.issubset(basic_stats.keys()):
        if TEST:
            print(f"Chybí některé základní údaje")
        return None
    
    if len(party_votes) < 29:  # volnější tolerance
        if TEST:
            print(f"Stránek stran podezřele málo ({len(party_votes)})")
        return None
        
    # Merging results into one dict
    result = basic_stats | party_votes

    return result if result else None




def get_precinct_detail_full(url_precinct: str) -> Optional[dict]:
    """
    Gets all the statistics for precicnt even
    if its separated into more parts
    """
    soup = load_url(url_precinct)
    if not soup:
        return None

    # If it can find header "sa2" it means the precinct is not
    # separated into more parts and we can continue
    if soup.find("td", headers="sa2"):
        return get_precinct_detail(soup)

    # If not, the precinct is separated into more parts
    # and we need to get the url of all parts first
    base_url = url_precinct.rsplit("/", 1)[0] + "/"
    precinct_parts = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "xvyber=" in href:
            precinct_parts.append(base_url + href)

    if not precinct_parts:
        return None

    # Now we can cumulate the result of all parts and
    # get the final result of the precinct
    cumulated_result = Counter()
    for part_url in precinct_parts:
        part_soup = load_url(part_url)
        data = get_precinct_detail(part_soup)
        if data:
            cumulated_result.update(data)
    return dict(cumulated_result)


def merge_dicts(precinct_info: dict, precinct_detail: dict) -> dict:
    """
    Merge two dicts containing basic info and detail info of precincts
    while also removing key url, which is now irrelevant
    """
    final = {k: v for k, v in precinct_info.items() if k != "url"} | precinct_detail
    return final


def collect_precinct_data(list_of_precincts: list[dict]) -> list[dict]:
    """
    Use list of precincts to aquire needed information from each one
    and returns them in the final list of dicts.
    """
    final_info = []
    for precinct in list_of_precincts:
        precinct_url = precinct["url"]
        precinct_detail = safe_get_precinct_detail(precinct_url)

        if not precinct_detail:
            if TEST:
                print(f"Cant load info in {precinct['location']} ({precinct_url})")
            continue

        precinct_merged = merge_dicts(precinct, precinct_detail)
        final_info.append(precinct_merged)

    return final_info


def safe_get_precinct_detail(precinct_url: str, retries=6, delay=6) -> Optional[dict]:
    """
    If the url cant be loaded due to the web response,
    try again after a short delay.
    """
    for i in range(retries):
        data = get_precinct_detail_full(precinct_url)
        if data is not None:
            return data
        if TEST:
            print(f"Try n. {i+1}/{retries} failed for {precinct_url}")

        # Increasing delay to give the web more time if it fails
        time.sleep(min(delay * (2 ** i), 150)) 
    return None


def convert_to_csv(district_info: list[dict], filename: str) -> None:
    """
    Create new (or rewrite existing) csv file.
    """
    if not district_info:
        print("No data to save.")
        return

    fieldnames = list(district_info[0].keys())

    with open(filename, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for record in district_info:
            writer.writerow(record)

    print(f"Ukládám do souboru: {filename}")


def is_valid_filename(file_name: str) -> bool:
    """
    Checks if filename doesn't contain invalid characters (mainly for Windows).
    """
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in file_name:
            return False
    return True


def is_valid_url(url: str) -> bool:
    """
    Checks whether the user's URL points to the expected site.
    """
    required_url_start_cz = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj="
    required_url_start_en = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=EN&xkraj="

    if not ((url.startswith(required_url_start_cz) or url.startswith(required_url_start_en)) and "&xnumnuts=" in url ):
        return False
    url_ending = url.split("&xnumnuts=")[-1]
    return True if url_ending.isdigit() and len(url_ending) == 4 else False


def main():
    if len(sys.argv) != 3:
        print("Chyba: Nezadal si požadovaný počet argumentů. Program bude ukončen.")
        return
    
    input_url = sys.argv[1]
    if not is_valid_url(input_url):
        print(f"Neplatné URL: {input_url}. Program bude ukončen.")
        return
    
    output_filename = sys.argv[2]
    if not is_valid_filename(output_filename):
        print(f"Neplatný název souboru: {output_filename}. Program bude ukončen.")
        return

    list_of_precincts = get_all_precincts(input_url)
    if not list_of_precincts:
        print("Na zadaném odkazu nebyly nalezené žádné obce. Program bude ukončen.")
        return

    final = collect_precinct_data(list_of_precincts)
    convert_to_csv(final, output_filename)
    print("Ukončuji program.")
    

if __name__ == "__main__":
    main()
 

