"""
BOE API Client Library

Spanish Official State Gazette (BOE) API client for accessing:
- Consolidated Legislation
- BOE Daily Summaries 
- BORME Commercial Registry Summaries
- Auxiliary Data (subjects, departments, etc.)

Documentation: https://www.boe.es/datosabiertos/api/api.php
"""

import requests
import json
from typing import Optional, Dict, List, Union, Any
from datetime import datetime, date
from urllib.parse import quote
import time
import logging


class BOEAPIError(Exception):
    """Custom exception for BOE API errors"""
    pass


class BOEAPIClient:
    """
    Client for the Spanish Official State Gazette (BOE) API
    
    Provides access to consolidated legislation, daily summaries,
    and auxiliary data from the Spanish government.
    """
    
    BASE_URL = "https://www.boe.es/datosabiertos/api"
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the BOE API client
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BOE-API-Client/1.0'
        })
        
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                     accept: str = "application/json") -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            url: API endpoint URL
            params: Query parameters
            accept: Accept header value
            
        Returns:
            Parsed JSON response
            
        Raises:
            BOEAPIError: If request fails after retries
        """
        headers = {"Accept": accept}
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Making request to {url}, attempt {attempt + 1}")
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                if accept == "application/json":
                    try:
                        data = response.json()
                    except ValueError as e:
                        raise BOEAPIError(f"Invalid JSON response: {e}")
                    
                    # Check API status
                    status = data.get("status", {})
                    if status.get("code") != "200":
                        raise BOEAPIError(f"API Error {status.get('code')}: {status.get('text')}")
                    
                    return data
                else:
                    return {"content": response.text, "status": {"code": "200"}}
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise BOEAPIError(f"Request failed after {self.max_retries + 1} attempts: {e}")
    
    def get_legislation_list(self, 
                           from_date: Optional[Union[str, date]] = None,
                           to_date: Optional[Union[str, date]] = None,
                           query: Optional[Dict] = None,
                           offset: int = 0,
                           limit: int = 50) -> Dict[str, Any]:
        """
        Get list of consolidated legislation
        
        Args:
            from_date: Start date for last update (YYYYMMDD or date object)
            to_date: End date for last update (YYYYMMDD or date object) 
            query: Search query in JSON format
            offset: First result to return
            limit: Maximum number of results (-1 for all)
            
        Returns:
            API response with legislation list
        """
        url = f"{self.BASE_URL}/legislacion-consolidada"
        params = {}
        
        if from_date:
            if isinstance(from_date, date):
                from_date = from_date.strftime("%Y%m%d")
            params["from"] = from_date
            
        if to_date:
            if isinstance(to_date, date):
                to_date = to_date.strftime("%Y%m%d")
            params["to"] = to_date
            
        if query:
            params["query"] = json.dumps(query)
            
        if offset > 0:
            params["offset"] = offset
            
        if limit != 50:
            params["limit"] = limit
            
        return self._make_request(url, params)
    
    def get_legislation_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        Get complete legislation document by ID
        
        Args:
            doc_id: Document identifier (e.g., "BOE-A-2015-10566")
            
        Returns:
            Complete legislation document in XML format
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}"
        return self._make_request(url, accept="application/xml")
    
    def get_legislation_metadata(self, doc_id: str) -> Dict[str, Any]:
        """
        Get legislation metadata by ID
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Legislation metadata
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}/metadatos"
        return self._make_request(url)
    
    def get_legislation_analysis(self, doc_id: str) -> Dict[str, Any]:
        """
        Get legislation analysis (subjects, notes, references)
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Legislation analysis data
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}/analisis"
        return self._make_request(url)
    
    def get_legislation_text(self, doc_id: str) -> Dict[str, Any]:
        """
        Get complete consolidated text of legislation
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Complete consolidated text in XML format
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}/texto"
        return self._make_request(url, accept="application/xml")
    
    def get_legislation_text_index(self, doc_id: str) -> Dict[str, Any]:
        """
        Get index of legislation text blocks
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Text block index
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}/texto/indice"
        return self._make_request(url)
    
    def get_legislation_text_block(self, doc_id: str, block_id: str) -> Dict[str, Any]:
        """
        Get specific text block from legislation
        
        Args:
            doc_id: Document identifier
            block_id: Block identifier
            
        Returns:
            Text block in XML format
        """
        url = f"{self.BASE_URL}/legislacion-consolidada/id/{doc_id}/texto/bloque/{block_id}"
        return self._make_request(url, accept="application/xml")
    
    def get_boe_summary(self, date_str: Union[str, date]) -> Dict[str, Any]:
        """
        Get BOE daily summary
        
        Args:
            date_str: Date in YYYYMMDD format or date object
            
        Returns:
            BOE summary for the specified date
        """
        if isinstance(date_str, date):
            date_str = date_str.strftime("%Y%m%d")
            
        url = f"{self.BASE_URL}/boe/sumario/{date_str}"
        return self._make_request(url)
    
    def get_borme_summary(self, date_str: Union[str, date]) -> Dict[str, Any]:
        """
        Get BORME daily summary
        
        Args:
            date_str: Date in YYYYMMDD format or date object
            
        Returns:
            BORME summary for the specified date
        """
        if isinstance(date_str, date):
            date_str = date_str.strftime("%Y%m%d")
            
        url = f"{self.BASE_URL}/borme/sumario/{date_str}"
        return self._make_request(url)
    
    def get_subjects(self) -> Dict[str, Any]:
        """Get auxiliary data: subject matters"""
        url = f"{self.BASE_URL}/datos-auxiliares/materias"
        return self._make_request(url)
    
    def get_scopes(self) -> Dict[str, Any]:
        """Get auxiliary data: scopes (national/regional)"""
        url = f"{self.BASE_URL}/datos-auxiliares/ambitos"
        return self._make_request(url)
    
    def get_consolidation_states(self) -> Dict[str, Any]:
        """Get auxiliary data: consolidation states"""
        url = f"{self.BASE_URL}/datos-auxiliares/estados-consolidacion"
        return self._make_request(url)
    
    def get_departments(self) -> Dict[str, Any]:
        """Get auxiliary data: government departments"""
        url = f"{self.BASE_URL}/datos-auxiliares/departamentos"
        return self._make_request(url)
    
    def get_ranks(self) -> Dict[str, Any]:
        """Get auxiliary data: legal document ranks"""
        url = f"{self.BASE_URL}/datos-auxiliares/rangos"
        return self._make_request(url)
    
    def get_previous_relations(self) -> Dict[str, Any]:
        """Get auxiliary data: previous legal relations"""
        url = f"{self.BASE_URL}/datos-auxiliares/relaciones-anteriores"
        return self._make_request(url)
    
    def get_subsequent_relations(self) -> Dict[str, Any]:
        """Get auxiliary data: subsequent legal relations"""
        url = f"{self.BASE_URL}/datos-auxiliares/relaciones-posteriores"
        return self._make_request(url)
    
    def search_legislation(self, 
                         title_contains: Optional[str] = None,
                         subject_codes: Optional[List[int]] = None,
                         department_code: Optional[int] = None,
                         rank_code: Optional[int] = None,
                         date_from: Optional[Union[str, date]] = None,
                         date_to: Optional[Union[str, date]] = None,
                         in_force_only: bool = False,
                         limit: int = 50) -> Dict[str, Any]:
        """
        Search legislation with common parameters
        
        Args:
            title_contains: Search term in title
            subject_codes: List of subject matter codes
            department_code: Government department code
            rank_code: Legal rank code
            date_from: Publication date from (YYYYMMDD or date)
            date_to: Publication date to (YYYYMMDD or date)
            in_force_only: Only return legislation still in force
            limit: Maximum results
            
        Returns:
            Search results
        """
        query_parts = []
        
        if title_contains:
            query_parts.append(f"titulo:{title_contains}")
            
        if subject_codes:
            subject_query = " or ".join([f"materia@codigo:{code}" for code in subject_codes])
            query_parts.append(f"({subject_query})")
            
        if department_code:
            query_parts.append(f"departamento@codigo:{department_code}")
            
        if rank_code:
            query_parts.append(f"rango@codigo:{rank_code}")
            
        if in_force_only:
            query_parts.append("vigencia_agotada:N")
        
        query = {}
        if query_parts:
            query_str = " and ".join(query_parts)
            query["query"] = {"query_string": {"query": query_str}}
        
        # Add date range if specified
        if date_from or date_to:
            range_query = {}
            if date_from:
                if isinstance(date_from, date):
                    date_from = date_from.strftime("%Y%m%d")
                range_query["gte"] = date_from
            if date_to:
                if isinstance(date_to, date):
                    date_to = date_to.strftime("%Y%m%d")
                range_query["lte"] = date_to
                
            if "query" not in query:
                query["query"] = {}
            query["query"]["range"] = {"fecha_publicacion": range_query}
        
        return self.get_legislation_list(query=query if query else None, limit=limit)


class BOEQueryBuilder:
    """Helper class to build complex search queries"""
    
    def __init__(self):
        self.query = {"query": {}}
        self.sort = []
    
    def title_contains(self, text: str) -> 'BOEQueryBuilder':
        """Add title search condition"""
        self._add_query_string(f"titulo:{text}")
        return self
    
    def subject_code(self, code: int) -> 'BOEQueryBuilder':
        """Add subject matter code condition"""
        self._add_query_string(f"materia@codigo:{code}")
        return self
    
    def department_code(self, code: int) -> 'BOEQueryBuilder':
        """Add department code condition"""
        self._add_query_string(f"departamento@codigo:{code}")
        return self
    
    def rank_code(self, code: int) -> 'BOEQueryBuilder':
        """Add legal rank code condition"""
        self._add_query_string(f"rango@codigo:{code}")
        return self
    
    def in_force_only(self) -> 'BOEQueryBuilder':
        """Only return legislation still in force"""
        self._add_query_string("vigencia_agotada:N")
        return self
    
    def date_range(self, from_date: Union[str, date], to_date: Union[str, date]) -> 'BOEQueryBuilder':
        """Add publication date range"""
        if isinstance(from_date, date):
            from_date = from_date.strftime("%Y%m%d")
        if isinstance(to_date, date):
            to_date = to_date.strftime("%Y%m%d")
            
        range_query = {"gte": from_date, "lte": to_date}
        self.query["query"]["range"] = {"fecha_publicacion": range_query}
        return self
    
    def sort_by(self, field: str, desc: bool = False) -> 'BOEQueryBuilder':
        """Add sort criteria"""
        order = "desc" if desc else "asc"
        self.sort.append({field: order})
        return self
    
    def _add_query_string(self, condition: str):
        """Add query string condition"""
        if "query_string" not in self.query["query"]:
            self.query["query"]["query_string"] = {"query": ""}
        
        current = self.query["query"]["query_string"]["query"]
        if current:
            self.query["query"]["query_string"]["query"] = f"{current} and {condition}"
        else:
            self.query["query"]["query_string"]["query"] = condition
    
    def build(self) -> Dict:
        """Build the final query"""
        result = dict(self.query)
        if self.sort:
            result["sort"] = self.sort
        return result


# Example usage and convenience functions
def search_data_protection_laws(client: BOEAPIClient) -> Dict[str, Any]:
    """Search for data protection related legislation"""
    query = (BOEQueryBuilder()
             .title_contains("proteccion")
             .title_contains("datos")
             .in_force_only()
             .sort_by("fecha_publicacion", desc=True)
             .build())
    
    return client.get_legislation_list(query=query, limit=10)


def get_latest_laws(client: BOEAPIClient, days: int = 30) -> Dict[str, Any]:
    """Get latest legislation from the past N days"""
    from_date = datetime.now().date().replace(day=1)  # Start of current month
    return client.get_legislation_list(from_date=from_date, limit=50)