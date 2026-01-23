import requests
import re

url = "https://www.nanosats.eu/database"
response = requests.get(url)
html_content = response.text

regex = r'<tr><td.*?<\/td><td.*?<\/td><td.*?>(.*?)<\/td>'

matches = re.findall(regex, html_content, re.DOTALL)

countries = set()
for match in matches:
    country = match.strip()
    if country:
        countries.add(country)

print(f"Number of unique countries with nanosatellites: {len(countries)}")
for country in sorted(countries):
    print(country)