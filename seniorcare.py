import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='capacity_extraction.log')

def get_cookies_from_selenium():
    """Use Selenium to get cookies from the site, then return them for use with requests."""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
        
        # Initialize the Chrome driver
        service = Service()  # Path to chromedriver if needed: Service('/path/to/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Visit the site to get cookies
        driver.get("https://www.seniorcare.com/")
        time.sleep(5)  # Wait for cookies to be set
        
        # Extract cookies from Selenium
        selenium_cookies = driver.get_cookies()
        
        # Convert Selenium cookies to requests format
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        
        # Close the browser
        driver.quit()
        
        # Add your known working cookies
        working_cookies = {
            '_pk_id.31.3c52': '0bd38cdee9336560.1746081017.',
            '_pk_ref.31.3c52': '%5B%22%22%2C%22%22%2C1746342595%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D',
            '_pk_ses.31.3c52': '1',
            '__eoi': 'ID=b3d35e83cbc72219:T=1746081086:RT=1746342896:S=AA-AfjbYMS3Mle04JKCkL0hWGH5X',
            'r': '1759643906',
            'datadome': 'msV4kVHFKM0G5xrSt5m_fjsV6iFhA1XKm~F268IZP51_pBhJeLcl6WArkkY3hB6BHEA3~DqkzZr2NhtIpue4JRuvgtzmD51QNh23QeBbF2sQ52t~l3DltQSpN605omd3',
        }
        
        # Merge the cookies, with working cookies taking precedence
        cookies_dict.update(working_cookies)
        
        return cookies_dict
    
    except Exception as e:
        logging.error(f"Error getting cookies from Selenium: {str(e)}")
        # Return the known working cookies if Selenium fails
        return {
            '_pk_id.31.3c52': '0bd38cdee9336560.1746081017.',
            '_pk_ref.31.3c52': '%5B%22%22%2C%22%22%2C1746342595%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D',
            '_pk_ses.31.3c52': '1',
            '__eoi': 'ID=b3d35e83cbc72219:T=1746081086:RT=1746342896:S=AA-AfjbYMS3Mle04JKCkL0hWGH5X',
            'r': '1759643906',
            'datadome': 'msV4kVHFKM0G5xrSt5m_fjsV6iFhA1XKm~F268IZP51_pBhJeLcl6WArkkY3hB6BHEA3~DqkzZr2NhtIpue4JRuvgtzmD51QNh23QeBbF2sQ52t~l3DltQSpN605omd3',
        }

def extract_capacity(url, cookies, headers):
    """Extract capacity from the given URL using requests with cookies."""
    print(f'extract for url : {url}')
    try:
        # Update referer to match the URL being accessed
        headers['referer'] = url
        
        # Make the request
        logging.info(f"Accessing URL: {url}")
        response = requests.get(url, cookies=cookies, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"Failed to access URL: {url}, Status code: {response.status_code}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the HTML content for debugging
        with open("output.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        
        # Find the capacity in the table
        capacity = None
        tables = soup.select('table.table-condensed')
        
        if tables:
            rows = tables[0].select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2 and 'Capacity' in cells[0].get_text():
                    capacity = cells[1].get_text().strip()
                    logging.info(f"Found capacity: {capacity}")
                    break
        
        # If we couldn't find it with the above method, try regex
        if capacity is None:
            capacity_match = re.search(r'<td><b>Capacity</b></td><td>(\d+)</td>', response.text)
            if capacity_match:
                capacity = capacity_match.group(1)
                logging.info(f"Found capacity using regex: {capacity}")
        
        return capacity
    
    except Exception as e:
        logging.error(f"Error extracting capacity: {str(e)}")
        return None

def process_csv_file(input_file='30000.csv', output_file='round_3_30000_facilities_final.csv'):
    """Process the CSV file and extract capacity for each facility with a source URL."""
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            logging.error(f"Input file not found: {input_file}")
            print(f"Error: Input file not found: {input_file}")
            return
        
        # Read the CSV file
        logging.info(f"Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        
        # Check if "Number of beds estimated" column exists
        if 'Number of beds estimated' not in df.columns:
            logging.warning("Column 'Number of beds estimated' not found. Creating it.")
            df['Number of beds estimated'] = None
        
        # Check if "source" column exists
        if 'source' not in df.columns:
            logging.error("Column 'source' not found in the input file.")
            print("Error: Column 'source' not found in the input file.")
            return
        
        # Create a copy of the original dataframe for output
        output_df = df.copy()
        
        # Get cookies from Selenium
        cookies = get_cookies_from_selenium()
        
        # Set headers
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-device-memory': '8',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-arch': '"arm"',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="135.0.7049.115", "Not-A.Brand";v="8.0.0.0", "Chromium";v="135.0.7049.115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        
        # Process each row
        total_rows = len(df)
        processed = 0
        updated = 0
        consecutive_failures = 0
        
        for index, row in df.iterrows():
            processed += 1
            
            # Get the source URL
            source_url = row.get('source')
            print(f'source_url : {source_url}')
            # Skip if no URL or not a SeniorCare.com URL
            if pd.isna(source_url) or 'seniorcare.com' not in str(source_url).lower():
                logging.info(f"Row {index+1}/{total_rows}: No SeniorCare.com URL, skipping")
                continue
            
            # Check if we already have capacity data
            current_capacity = row.get('Number of beds estimated')
            if pd.notna(current_capacity) and str(current_capacity).strip() and str(current_capacity).strip() != 'Unknown':
                logging.info(f"Row {index+1}/{total_rows}: Already has capacity data ({current_capacity}), skipping")
                continue
            
            # Log progress
            facility_name = row.get('Facility name', f"Row {index+1}")
            logging.info(f"Row {index+1}/{total_rows}: Processing {facility_name}")
            print(f"Row {index+1}/{total_rows}: Processing {facility_name}")
            
            # Extract capacity
            capacity = extract_capacity(source_url, cookies, headers)
            
            # Check if we're being blocked
            if capacity is None:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logging.warning("Multiple consecutive failures detected. Refreshing cookies...")
                    cookies = get_cookies_from_selenium()  # Get fresh cookies
                    consecutive_failures = 0
                    time.sleep(random.uniform(60, 120))  # Long pause before continuing
            else:
                consecutive_failures = 0
            
            # Update the dataframe if capacity was found
            if capacity:
                try:
                    # Convert to integer if possible
                    capacity_int = int(capacity)
                    output_df.at[index, 'Number of beds estimated'] = capacity_int
                except ValueError:
                    # If not a valid integer, store as string
                    output_df.at[index, 'Number of beds estimated'] = capacity
                
                logging.info(f"Row {index+1}/{total_rows}: Updated capacity for {facility_name}: {capacity}")
                print(f"Row {index+1}/{total_rows}: Updated capacity for {facility_name}: {capacity}")
                updated += 1
            else:
                logging.warning(f"Row {index+1}/{total_rows}: Could not find capacity for {facility_name}")
                print(f"Row {index+1}/{total_rows}: Could not find capacity for {facility_name}")
            
            # Save progress after each row
            output_df.to_csv(output_file, index=False)
            
            # Add a delay between requests to avoid rate limiting
            if processed < total_rows:
                delay = random.uniform(15, 30)  # Delay between requests
                logging.info(f"Waiting {delay:.2f} seconds before next request...")
                print(f"Waiting {delay:.2f} seconds before next request...")
                time.sleep(delay)
        
        # Final save
        output_df.to_csv(output_file, index=False)
        logging.info(f"Processing complete. Processed {processed} rows, updated {updated} facilities.")
        print(f"Processing complete. Processed {processed} rows, updated {updated} facilities.")
        print(f"Results saved to {output_file}")
    
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")
        print(f"Error processing CSV file: {str(e)}")

if __name__ == "__main__":
    process_csv_file()
