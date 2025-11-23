# crypto_tracker.py - Cryptocurrency Price Tracker (improved)
import time
import sys
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Optional nice table formatter
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ModuleNotFoundError:
    HAS_TABULATE = False

class CryptocurrencyPriceTracker:
    def __init__(self, headless=True, timeout=20):
        self.headless = headless
        self.driver = None
        self.csv_file = "crypto_data.csv"
        self.timeout = timeout
        self.setup_driver()

    def setup_driver(self):
        print("🚀 Starting Cryptocurrency Tracker...")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")  # newer headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("window-size=1920,1080")
        # set a common user-agent to reduce bot detection:
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def scrape_crypto_data(self, top_n=10):
        url = "https://coinmarketcap.com/"
        print(f"📡 Connecting to {url}")
        self.driver.get(url)

        # Wait for rows to appear in any table body
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody/tr"))
            )
        except Exception as e:
            print(f"❌ Timeout waiting for coin rows: {e}")
            return []

        # a short pause to let dynamic content settle
        time.sleep(2)

        crypto_data = []
        # select the first top_n rows
        rows = self.driver.find_elements(By.XPATH, "//table//tbody/tr")[:top_n]

        for i, row in enumerate(rows):
            try:
                # gather cell texts; CoinMarketCap changes its DOM often, so be defensive
                cells = row.find_elements(By.TAG_NAME, "td")
                # best-effort: find name, price, change, market cap
                # typical layout: [rank, name/coin, price, 24h, 7d, market cap, volume, circulating supply] but may vary
                name = ""
                price = ""
                change_24h = ""
                market_cap = ""

                # Name (try: second or third cell)
                if len(cells) >= 3:
                    name = cells[2].text.split("\n")[0].strip()
                elif len(cells) >= 2:
                    name = cells[1].text.split("\n")[0].strip()

                # Price (search for a $ in cells)
                for c in cells:
                    txt = c.text.strip()
                    if txt.startswith("$"):
                        price = txt.replace("$", "").replace(",", "").split("\n")[0]
                        break

                # 24h change (a value with %)
                for c in cells:
                    txt = c.text.strip()
                    if txt.endswith("%") and len(txt) < 10:  # heuristic
                        change_24h = txt.replace("%", "").replace(",", "")
                        break

                # Market cap (often contains $ and large number)
                for c in reversed(cells):
                    txt = c.text.strip()
                    if txt.startswith("$"):
                        # prefer large numbers near the end - heuristic
                        market_cap = txt.replace("$", "").replace(",", "").split("\n")[0]
                        break

                crypto_info = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Rank": i + 1,
                    "Name": name or f"Unknown-{i+1}",
                    "Price": price or "N/A",
                    "24h Change (%)": change_24h or "N/A",
                    "Market Cap": market_cap or "N/A",
                }
                crypto_data.append(crypto_info)
                print(f"✅ {crypto_info['Rank']}. {crypto_info['Name']}: ${crypto_info['Price']}")
            except Exception as e:
                print(f"❌ Error with row {i+1}: {e}")
                continue

        return crypto_data

    def close(self):
        if self.driver:
            self.driver.quit()
            print("🔚 Browser closed")


def main():
    print("✅ Script starting...")

    tracker = None
    try:
        tracker = CryptocurrencyPriceTracker(headless=True)
        crypto_data = tracker.scrape_crypto_data(top_n=10)

        if crypto_data:
            print(f"\n📊 Total cryptocurrencies tracked: {len(crypto_data)}")

            # Convert to DataFrame for tabular display
            df = pd.DataFrame(crypto_data)

            # Print table in terminal using tabulate if available
            print("\n📋 Cryptocurrency Data:\n")
            if HAS_TABULATE:
                print(tabulate(df, headers="keys", tablefmt="github", showindex=False))
            else:
                # fallback to pandas pretty print
                print(df.to_string(index=False))

            # Save to CSV
            df.to_csv("crypto_data.csv", index=False)
            print("\n💾 Data saved to crypto_data.csv")
        else:
            print("❌ Failed to scrape data or no data found")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if tracker:
            tracker.close()


if __name__ == "__main__":
    main()
