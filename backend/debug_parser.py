import sys
import os
sys.path.append(os.getcwd())
import logging
import xml.etree.ElementTree as ET
from app.shared.placsp_client import PLACSPClient
from app.shared.codice_parser import CODICEParser
from app.config import get_settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_placsp_entry():
    settings = get_settings()
    client = PLACSPClient()
    parser = CODICEParser()
    
    print(f"Fetching feed from {settings.placsp_feed_url}...")
    entries, _ = client.fetch_feed(settings.placsp_feed_url)
    
    if not entries:
        print("No entries found.")
        return

    # Parse all entries
    print(f"\nFound {len(entries)} entries. Searching for 17061261:")
    found = False
    for i, entry in enumerate(entries):
        data = parser.parse_entry(entry)
        if '17061261' in str(data.get('id')):
            print(f"FOUND! Entry {i+1}: ID={data.get('id')}, Link={data.get('link')}")
            found = True
            break
    
    if not found:
        print("Grant 17061261 NOT found in the first page of the feed.")

if __name__ == "__main__":
    debug_placsp_entry()
