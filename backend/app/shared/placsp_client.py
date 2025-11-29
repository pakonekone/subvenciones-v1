"""
PLACSP Client Library

Client for accessing the Public Sector Contracting Platform (PLACSP)
via Atom Syndication Format.
"""

import requests
import logging
import time
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

class PLACSPClient:
    """
    Client for interacting with PLACSP Atom feeds.
    """
    
    NAMESPACES = {
        'atom': 'http://www.w3.org/2005/Atom',
        'at': 'http://purl.org/atompub/tombstones/1.0',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'dgpe': 'http://contrataciondelestado.es/codice/placsp',
        'n2016': 'http://contrataciondelestado.es/codice/cl/2.04/Nuts-2016'
    }

    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PLACSP-Client/1.0'
        })
        self.logger = logging.getLogger(__name__)

    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Fetching {url}, attempt {attempt + 1}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise e

    def fetch_feed(self, url: str) -> Tuple[List[ET.Element], Optional[str]]:
        """
        Fetch and parse an Atom feed.
        
        Returns:
            Tuple containing:
            - List of <entry> elements (as xml.etree.ElementTree.Element)
            - URL of the 'next' page (if available)
        """
        response = self._make_request(url)
        
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse XML from {url}: {e}")
            raise

        # Find entries
        entries = root.findall('atom:entry', self.NAMESPACES)
        
        # Find next link
        next_link = None
        links = root.findall('atom:link', self.NAMESPACES)
        for link in links:
            if link.get('rel') == 'next':
                next_link = link.get('href')
                break
                
        return entries, next_link

    def get_entry_xml(self, entry: ET.Element) -> Optional[ET.Element]:
        """
        Extract the CODICE XML content from an Atom entry.
        The content is usually inside <content> tag, but might need parsing if it's escaped.
        """
        # In PLACSP, the CODICE XML is often embedded directly or inside a content tag.
        # Based on specs, it seems to be inside the entry.
        # We'll return the entry itself or the specific child if we identify a container.
        return entry

