import re
import time

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import NUM_LISTINGS
from items import Apartment

BASE_URL = "https://realtylink.org/en/properties~for-rent?uc=1"


class Scraper:

    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        )
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def get_all_rents(self) -> list:
        self.driver.get(BASE_URL)
        time.sleep(2)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "property-thumbnail-item"))
        )
        links = []

        while len(links) < NUM_LISTINGS:
            apartments = self.driver.find_elements(By.CLASS_NAME, "property-thumbnail-item")
            for apartment in apartments:
                link = apartment.find_element(By.TAG_NAME, "a").get_attribute("href")
                links.append(link)
                if len(links) >= NUM_LISTINGS:
                    break
            if len(links) < NUM_LISTINGS:
                self.click_next_page()

        return links[:NUM_LISTINGS]

    def click_next_page(self) -> None:
        toggle = self.driver.find_element(By.CLASS_NAME, "pager")
        next_button = toggle.find_element(By.CLASS_NAME, "next")
        if "inactive" not in next_button.get_attribute("class"):
            next_button.click()
            time.sleep(2)

    def scrape_rent(self, url: str) -> Apartment | None:
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1 [data-id='PageTitle']"))
            )
        except (TimeoutException, NoSuchElementException):
            return None

        try:
            location = self.driver.find_element(By.CLASS_NAME, "pt-1").text
            region = ", ".join(location.split(", ")[2:])
            address = ", ".join(location.split(", ")[:2])
        except NoSuchElementException:
            location, region, address = "", "", ""

        return Apartment(
                link=url,
                title=self.get_title(),
                region=region,
                address=address,
                description=self.get_description(),
                pictures=self.extract_pictures(),
                date="published recently",
                price=self.get_price(),
                room_amount=self.get_room_amount(),
                square=self.get_square(),
            )

    def get_title(self) -> str:
        try:
            return self.driver.find_element(By.CSS_SELECTOR, "h1 [data-id='PageTitle']").text
        except NoSuchElementException:
            return ""

    def get_price(self) -> int | str:
        try:
            return int(self.driver.find_element(
                By.CSS_SELECTOR, "div.row.property-tagline > div.d-none.d-sm-block.house-info > "
                                 "div > div.price-container > div.price.text-right > span:nth-child(6)"
            ).text.replace(",", "").replace("$", "").split()[0])
        except NoSuchElementException:
            return ""

    def get_description(self) -> str:
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR, "div.grid_3 > div.row.description-row > div > div:nth-child(2)"
            ).text
        except NoSuchElementException:
            return ""

    def get_room_amount(self) -> int | str:
        try:
            return int(self.driver.find_element(
                By.CSS_SELECTOR, "div.grid_3 > div.col-lg-12.description > div.row.teaser > div.col-lg-3.col-sm-6.cac"
            ).text.split()[0])
        except NoSuchElementException:
            return ""

    def get_square(self) -> int | str:
        try:
            return int(self.driver.find_element(By.CLASS_NAME, "carac-value").text.replace(",", "").split()[0])
        except NoSuchElementException:
            return ""

    def extract_pictures(self) -> list:
        try:
            javascript_block = self.driver.find_element(
                By.XPATH, '//script[contains(text(), "window.MosaicPhotoUrls")]'
            ).get_attribute('innerHTML')
            pictures_match = re.search(r"window\.MosaicPhotoUrls = (\[.*?]);", javascript_block)
            if pictures_match:
                pictures = eval(pictures_match.group(1))
                return pictures
        except Exception:
            return []

    def close(self) -> None:
        self.driver.quit()
