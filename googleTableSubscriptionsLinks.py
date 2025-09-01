import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

from pyasn1.type.univ import Null
from requests.utils import get_encoding_from_headers

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gen-lang-client-0738187198-4dffb70e5f2b.json", scope)
client = gspread.authorize(creds)

sheet = client.open("KOL ProCrypto").sheet1


async def read_all_data():
    """Асинхронна функція для читання даних з Google таблиці"""
    data = await asyncio.to_thread(sheet.get_all_records)
    return data

async def get_all_links():
    data_list = []
    data = await read_all_data()
    for x in data:
        if (x["Link"] != "" and  "https" in x["Link"]):
            data_list.append(x["Link"])
    return data_list



if __name__ == "__main__":
    data = asyncio.run(get_all_links())
    print(data)
    



