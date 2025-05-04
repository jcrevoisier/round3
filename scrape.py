import csv
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote
import pickle
import os

def extract_location_from_address(address):
    """Extract city and state from address."""
    # Common pattern: city, state zip
    match = re.search(r',\s*([^,]+),\s*([A-Z]{2})\s*\d', address)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # Try another pattern
    match = re.search(r',\s*([^,]+),\s*([A-Z]{2})', address)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    return "", ""

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    chrome_options = Options()
    # Don't use headless mode so you can solve the CAPTCHA
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def solve_captcha_manually(driver):
    """Allow user to manually solve CAPTCHA."""
    print("CAPTCHA detected! Please solve it manually in the browser window.")
    print("After solving the CAPTCHA, press Enter to continue...")
    input("Press Enter after solving the CAPTCHA...")
    
    # Save cookies after CAPTCHA is solved
    pickle.dump(driver.get_cookies(), open("google_cookies.pkl", "wb"))
    print("Cookies saved for future use.")

def is_valid_sca_url(url):
    """Check if the URL is a valid SeniorCareAuthority.com URL."""
    if not url or not isinstance(url, str):
        return False
        
    # Must be a SeniorCareAuthority.com URL
    if not url.startswith("https://www.seniorcareauthority.com/"):
        return False
    
    # Exclude generic pages like agreement-to-be-contacted
    if "agreement-to-be-contacted" in url:
        return False
    
    # Exclude Google search URLs
    if "google.com/search" in url:
        return False
    
    # Exclude account pages
    if "accounts." in url:
        return False
    
    return True

def search_and_extract_url(driver, query):
    """Perform a Google search and extract SeniorCareAuthority.com URLs."""
    encoded_query = quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page to load
        
        # Check if CAPTCHA is present
        if "unusual traffic" in driver.page_source.lower() or "captcha" in driver.page_source.lower():
            print("CAPTCHA detected!")
            solve_captcha_manually(driver)
            # Reload the page after solving CAPTCHA
            driver.get(url)
            time.sleep(2)
        
        # Check if we're redirected to a login page
        current_url = driver.current_url
        if "accounts.google.com" in current_url:
            print("Redirected to login page. Please solve the CAPTCHA or login.")
            solve_captcha_manually(driver)
            # Try the search again
            driver.get(url)
            time.sleep(2)
        
        # Find all links in search results
        # Use a more specific selector to find only the main search result links
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
        
        # If the above selector doesn't work, try this alternative
        if not search_results:
            search_results = driver.find_elements(By.CSS_SELECTOR, "a[href*='seniorcareauthority.com']")
        
        # If still no results, try a more general approach
        if not search_results:
            search_results = driver.find_elements(By.TAG_NAME, "a")
        
        # Look for valid seniorcareauthority.com links
        for link in search_results:
            href = link.get_attribute("href")
            if href and is_valid_sca_url(href):
                print(f"Found URL: {href}")
                return href
        
        # If no links found, try to extract from the page source
        page_source = driver.page_source
        sca_urls = re.findall(r'href="(https://www\.seniorcareauthority\.com[^"]+)"', page_source)
        
        if sca_urls:
            for sca_url in sca_urls:
                if is_valid_sca_url(sca_url):
                    print(f"Found URL from page source: {sca_url}")
                    return sca_url
        
        print("No valid SeniorCareAuthority.com URL found in search results.")
        return "Not found"
    
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return "Error"

def main():
    input_file = 'round_2_10000_facilities.csv'
    output_file = 'round_2_10000_facilities_final.csv'
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Add a new column for SeniorCareAuthority URLs
    if 'SeniorCareAuthority URL' not in df.columns:
        df['SeniorCareAuthority URL'] = "Not searched"
    
    # Process each facility
    index = 0
    while index < len(df):
        # Set up a new WebDriver for each batch of searches to avoid session issues
        driver = None
        try:
            # Skip already processed rows with valid URLs
            current_url = df.at[index, 'SeniorCareAuthority URL']
            if current_url not in ["Not searched", "Error", "Not found"] and is_valid_sca_url(current_url):
                print(f"Skipping already processed row {index+1}")
                index += 1
                continue
            
            # Initialize the driver if needed
            if driver is None:
                driver = setup_driver()
                # Load cookies if available
                if os.path.exists("google_cookies.pkl"):
                    driver.get("https://www.google.com")
                    cookies = pickle.load(open("google_cookies.pkl", "rb"))
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except Exception as e:
                            print(f"Error adding cookie: {e}")
                    driver.refresh()
                    print("Cookies loaded from file.")
            
            facility_name = df.at[index, 'Facility name']
            address = df.at[index, 'Full Address']
            
            # Extract city and state from address
            city, state = extract_location_from_address(address)
            
            if city and state:
                # Construct search query
                search_query = f"site:seniorcareauthority.com {facility_name} in {city} {state}"
                print(f"Row {index+1}/{len(df)}: Searching for: {search_query}")
                
                # Perform search and extract URL
                sca_url = search_and_extract_url(driver, search_query)
                
                # Update the dataframe only if it's a valid URL
                if sca_url != "Not found" and sca_url != "Error" and not is_valid_sca_url(sca_url):
                    sca_url = "Not found"
                
                df.at[index, 'SeniorCareAuthority URL'] = sca_url
                
                # Save progress after each search
                df.to_csv(output_file, index=False)
                
                # Sleep to avoid rate limiting
                time.sleep(3)
            else:
                print(f"Could not extract location from address: {address}")
                df.at[index, 'SeniorCareAuthority URL'] = "Location extraction failed"
                df.to_csv(output_file, index=False)
            
            # Move to the next facility
            index += 1
            
        except Exception as e:
            if "invalid session id" in str(e).lower() or "session deleted" in str(e).lower():
                print(f"Session error occurred: {e}")
                print("Restarting WebDriver...")
                
                # Close the current driver if it exists
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                
                driver = None
                
                # Don't increment index so we retry the current facility
                # Save progress before retrying
                df.to_csv(output_file, index=False)
                
                # Wait a bit before retrying
                time.sleep(5)
            else:
                # For other errors, log and continue to the next facility
                print(f"Unexpected error: {e}")
                df.at[index, 'SeniorCareAuthority URL'] = "Error"
                df.to_csv(output_file, index=False)
                index += 1
                
                # Close the current driver if it exists
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                
                driver = None
                time.sleep(5)
        
        finally:
            # Close the WebDriver at the end of each batch
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # Clean up any invalid URLs in the final results
    for index, row in df.iterrows():
        current_url = df.at[index, 'SeniorCareAuthority URL']
        if current_url not in ["Not searched", "Error", "Not found", "Location extraction failed"] and not is_valid_sca_url(current_url):
            df.at[index, 'SeniorCareAuthority URL'] = "Not found"
    
    # Save final results
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()

