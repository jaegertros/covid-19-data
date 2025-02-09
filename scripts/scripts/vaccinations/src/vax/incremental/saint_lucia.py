import os
import re
import requests
import locale

from bs4 import BeautifulSoup
import pandas as pd

from vax.utils.incremental import enrich_data, increment, clean_date, clean_count


def read(source: str) -> pd.Series:
    return connect_parse_data(source)


def connect_parse_data(source: str) -> pd.Series:

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    soup = BeautifulSoup(requests.get(source, headers=headers).content, "html.parser")

    people_vaccinated = soup.find_all(class_="repart-stlucia")[0].text
    people_vaccinated = clean_count(people_vaccinated)

    people_fully_vaccinated = soup.find_all(class_="repart-stlucia")[1].text
    people_fully_vaccinated = clean_count(people_fully_vaccinated)

    total_vaccinations = people_vaccinated + people_fully_vaccinated

    date = soup.find(class_="h2-blue").text
    date = re.search(r"\w+ +\d+, +202\d", date).group(0)
    date = clean_date(date, "%B %d, %Y")

    data = {
        "total_vaccinations": total_vaccinations,
        "people_vaccinated": people_vaccinated,
        "people_fully_vaccinated": people_fully_vaccinated,
        "date": date,
    }
    return pd.Series(data=data)


def enrich_location(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "location", "Saint Lucia")


def enrich_vaccine(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "vaccine", "Oxford/AstraZeneca")


def enrich_source(ds: pd.Series) -> pd.Series:
    return enrich_data(ds, "source_url", "https://www.covid19response.lc/")


def pipeline(ds: pd.Series) -> pd.Series:
    return (
        ds
        .pipe(enrich_location)
        .pipe(enrich_vaccine)
        .pipe(enrich_source)
    )


def main(paths):
    locale.setlocale(locale.LC_TIME, "en_GB")
    source = "https://www.covid19response.lc/"
    data = read(source).pipe(pipeline)
    increment(
        paths=paths,
        location=data["location"],
        total_vaccinations=data["total_vaccinations"],
        people_vaccinated=data["people_vaccinated"],
        people_fully_vaccinated=data["people_fully_vaccinated"],
        date=data["date"],
        source_url=data["source_url"],
        vaccine=data["vaccine"]
    )


if __name__ == "__main__":
    main()
