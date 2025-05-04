import requests
from bs4 import BeautifulSoup
import re 

cookies = {
    'datadome': 'yem8TFP2rAPVjHlngAbENZrGIN1zW8hmJQIrvthgP~GRh1i9d9WVpR6UYhxsRzSIvb48Xw~LJ41e5_Aa6y7STqlzUVPuplFliHLPTRMKqZwWyDMlquT3iKLErIYhnwuW',
}

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',}

response = requests.get(
    'https://www.seniorcare.com/assisted-living/ct/hartford/avery-heights-assisted-living-services-agency/11450/',
    cookies=cookies,
    headers=headers,
)
print(response)
# Parse the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Find the capacity in the table
capacity = None
tables = soup.select('table.table-condensed')

if tables:
    rows = tables[0].select('tr')
    for row in rows:
        cells = row.select('td')
        if len(cells) >= 2 and 'Capacity' in cells[0].get_text():
            capacity = cells[1].get_text().strip()
            print(f"Found capacity: {capacity}")
            break

# If we couldn't find it with the above method, try regex
if capacity is None:
    capacity_match = re.search(r'<td><b>Capacity</b></td><td>(\d+)</td>', response.text)
    if capacity_match:
        capacity = capacity_match.group(1)
        print(f"Found capacity using regex: {capacity}")

with open("output.html", "w", encoding="utf-8") as file:
    file.write(response.text)