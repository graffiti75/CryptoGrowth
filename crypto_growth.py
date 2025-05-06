import requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration

# Fetch data from CoinMarketCap
url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
headers = {"Accepts": "application/json", "X-CMC_PRO_API_KEY": CMC_API_KEY}
params = {"limit": 300, "convert": "USD"}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    cryptos = response.json()["data"]
    top_growers = sorted(cryptos, key=lambda x: x["quote"]["USD"].get("percent_change_24h", 0), reverse=True)[:7]
else:
    print(f"Error: {response.status_code}, {response.text}")
    exit()

# Current date and time
now = datetime.now()
date = now.strftime("%d/%m/%Y")
hour = now.strftime("%H:%M")

# Prepare data line
line = f"{date};{hour};"
values = [date, hour]
for crypto in top_growers:
    line += f"{crypto['name']};{crypto['quote']['USD']['price']};{crypto['quote']['USD']['percent_change_24h']};"
    values.extend([crypto["name"], crypto["quote"]["USD"]["price"], crypto["quote"]["USD"]["percent_change_24h"]])

# Write to .txt file (prepend new line)
try:
    with open("crypto_data.txt", "r") as f:
        existing_content = f.read()
except FileNotFoundError:
    existing_content = ""
with open("crypto_data.txt", "w") as f:
    f.write(line + "\n" + existing_content)

# Write to Google Sheets (insert at first row)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Insert a new row at the top
service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={
        "requests": [{
            "insertDimension": {
                "range": {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "inheritFromBefore": False
            }
        }]
    }
).execute()

# Update the first row with new data
body = {'values': [values]}
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A1:W1',
    valueInputOption='RAW',
    body=body
).execute()