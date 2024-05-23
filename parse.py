import json
from dataclasses import asdict

from scraper import Scraper
from items import Apartment


def write_apartments_to_json(output_json_path: str, apartments: list[Apartment]) -> None:
    with open(output_json_path, "w", encoding="utf-8") as file:
        json_data = [asdict(apartment) for apartment in apartments if apartment is not None]
        json.dump(json_data, file, ensure_ascii=False, indent=4)


def main(output_json_path: str) -> None:
    scraper = Scraper()
    apartment_links = scraper.get_all_rents()
    apartments = []
    for link in apartment_links:
        apartment = scraper.scrape_rent(link)
        if apartment:
            apartments.append(apartment)
    write_apartments_to_json(output_json_path, apartments)
    scraper.close()


if __name__ == "__main__":
    main("apartments.json")
