"""
BDNS API Client

Robust client for interacting with the BDNS (Base de Datos Nacional de Subvenciones) API.
Includes retry logic, error handling, and rate limiting.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .bdns_models import (
    BDNSSearchParams,
    BDNSSearchResponse,
    BDNSConvocatoriaDetail,
    BDNSConvocatoriaSummary,
    BDNSNonprofitAnalysis
)


logger = logging.getLogger(__name__)


class BDNSAPIError(Exception):
    """Base exception for BDNS API errors"""
    pass


class BDNSAPIClient:
    """Client for BDNS API with robust error handling"""

    BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"

    # Nonprofit keywords for filtering
    NONPROFIT_KEYWORDS = {
        'primary': [
            "sin ánimo de lucro",
            "sin animo de lucro",
            "sin fines de lucro",
            "entidad sin ánimo de lucro",
            "entidad sin animo de lucro",
            "organización sin ánimo de lucro",
            "organizacion sin animo de lucro"
        ],
        'entity_types': [
            "fundación",
            "fundacion",
            "asociación",
            "asociacion",
            "ONG",
            "entidad social",
            "tercer sector",
            "cooperativa social"
        ],
        'excluded': [
            "con ánimo de lucro",
            "empresa privada",
            "sociedad mercantil",
            "sociedad anónima",
            "sociedad limitada"
        ]
    }

    def __init__(self, timeout: int = 30, max_retries: int = 3, backoff_factor: float = 0.5):
        """
        Initialize BDNS API client

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
        """
        self.timeout = timeout
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'BDNS-API-Client/1.0'
        })

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests

        logger.info("✅ BDNS API Client initialized")

    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request with error handling

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            BDNSAPIError: If request fails
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            logger.debug(f"🔍 Request: GET {endpoint}")
            if params:
                logger.debug(f"📋 Parameters: {params}")

            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"✅ Success: {response.status_code}")
                return data
            else:
                error_msg = f"BDNS API error {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ {error_msg}")
                raise BDNSAPIError(error_msg)

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"⏱️  {error_msg}")
            raise BDNSAPIError(error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"🔌 {error_msg}")
            raise BDNSAPIError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request exception: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise BDNSAPIError(error_msg)

        except ValueError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error(f"📄 {error_msg}")
            raise BDNSAPIError(error_msg)

    def search_convocatorias(self, params: BDNSSearchParams) -> BDNSSearchResponse:
        """
        Search for convocatorias

        Args:
            params: Search parameters

        Returns:
            Search response with results

        Raises:
            BDNSAPIError: If search fails
        """
        try:
            params_dict = params.to_params_dict()
            data = self._make_request('/convocatorias/busqueda', params_dict)

            response = BDNSSearchResponse(**data)
            logger.info(f"📊 Found {response.totalElements} convocatorias")

            return response

        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            raise BDNSAPIError(f"Search failed: {str(e)}")

    def get_convocatoria_detail(self, num_conv: str, vpd: str = "GE") -> Optional[BDNSConvocatoriaDetail]:
        """
        Get detailed information for a convocatoria

        Args:
            num_conv: Convocatoria number
            vpd: Portal ID (default: GE)

        Returns:
            Detailed convocatoria data or None if not found

        Raises:
            BDNSAPIError: If request fails
        """
        try:
            params = {
                'numConv': num_conv,
                'vpd': vpd
            }

            data = self._make_request('/convocatorias', params)

            if 'codigoBDNS' in data:
                detail = BDNSConvocatoriaDetail(**data)
                logger.info(f"📄 Retrieved detail for {num_conv}")
                return detail
            else:
                logger.warning(f"⚠️  No detail found for {num_conv}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get detail for {num_conv}: {str(e)}")
            raise BDNSAPIError(f"Get detail failed: {str(e)}")

    def get_latest_convocatorias(self, page: int = 0, page_size: int = 50) -> BDNSSearchResponse:
        """
        Get latest convocatorias

        Args:
            page: Page number
            page_size: Results per page

        Returns:
            Search response with latest convocatorias
        """
        params = BDNSSearchParams(
            page=page,
            pageSize=page_size,
            order='fechaRecepcion',
            direccion='desc'
        )

        return self.search_convocatorias(params)

    def search_nonprofit(self, page: int = 0, page_size: int = 50,
                        fecha_desde: Optional[str] = None,
                        fecha_hasta: Optional[str] = None) -> BDNSSearchResponse:
        """
        Search for nonprofit organization convocatorias

        Args:
            page: Page number
            page_size: Results per page
            fecha_desde: Start date (dd/MM/yyyy)
            fecha_hasta: End date (dd/MM/yyyy)

        Returns:
            Search response filtered for nonprofits
        """
        params = BDNSSearchParams(
            page=page,
            pageSize=page_size,
            order='fechaRecepcion',
            direccion='desc',
            descripcion="sin ánimo de lucro",  # Primary filter
            descripcionTipoBusqueda=1,  # All words
            fechaDesde=fecha_desde,
            fechaHasta=fecha_hasta
        )

        logger.info(f"🔍 Searching for nonprofit convocatorias (page {page})")
        return self.search_convocatorias(params)

    def analyze_nonprofit(self, text: str) -> BDNSNonprofitAnalysis:
        """
        Analyze text to determine if it's for nonprofit organizations

        Args:
            text: Text to analyze (title + description)

        Returns:
            Nonprofit analysis result
        """
        text_lower = text.lower()

        analysis = BDNSNonprofitAnalysis(
            is_nonprofit=False,
            confidence_score=0.0,
            primary_keywords_found=[],
            entity_type_keywords_found=[],
            exclusion_keywords_found=[],
            has_exclusions=False,
            matched_keywords=[]
        )

        # Check primary nonprofit keywords (REQUIRED)
        for keyword in self.NONPROFIT_KEYWORDS['primary']:
            if keyword.lower() in text_lower:
                analysis.primary_keywords_found.append(keyword)
                analysis.matched_keywords.append(keyword)
                analysis.confidence_score += 0.4

        # Check entity type keywords (POSITIVE INDICATOR)
        for keyword in self.NONPROFIT_KEYWORDS['entity_types']:
            if keyword.lower() in text_lower:
                analysis.entity_type_keywords_found.append(keyword)
                analysis.matched_keywords.append(keyword)
                analysis.confidence_score += 0.15

        # Check exclusion keywords (NEGATIVE INDICATOR)
        for keyword in self.NONPROFIT_KEYWORDS['excluded']:
            if keyword.lower() in text_lower:
                analysis.exclusion_keywords_found.append(keyword)
                analysis.has_exclusions = True
                analysis.confidence_score -= 0.5

        # Determine if nonprofit based on rules:
        # 1. Must have at least one primary keyword
        # 2. Must NOT have exclusion keywords
        # 3. Confidence score must be > 0.3
        if analysis.primary_keywords_found and not analysis.has_exclusions and analysis.confidence_score > 0.3:
            analysis.is_nonprofit = True

        # Cap confidence score
        analysis.confidence_score = max(0.0, min(1.0, analysis.confidence_score))

        return analysis

    def filter_nonprofit_results(self, convocatorias: List[BDNSConvocatoriaSummary],
                                fetch_details: bool = False) -> List[Dict[str, Any]]:
        """
        Filter convocatorias for nonprofit organizations

        Args:
            convocatorias: List of convocatorias to filter
            fetch_details: Whether to fetch full details for each

        Returns:
            List of filtered convocatorias with nonprofit analysis
        """
        filtered = []

        for conv in convocatorias:
            # Analyze text
            text = f"{conv.descripcion} {conv.nivel1} {conv.nivel2 or ''}"
            analysis = self.analyze_nonprofit(text)

            if analysis.is_nonprofit:
                result = {
                    'convocatoria': conv.dict(),
                    'nonprofit_analysis': analysis.dict()
                }

                # Fetch details if requested
                if fetch_details:
                    try:
                        detail = self.get_convocatoria_detail(conv.numeroConvocatoria)
                        if detail:
                            result['detail'] = detail.dict()
                    except Exception as e:
                        logger.warning(f"⚠️  Could not fetch detail for {conv.numeroConvocatoria}: {e}")

                filtered.append(result)

        logger.info(f"✅ Filtered {len(filtered)} nonprofit convocatorias from {len(convocatorias)}")
        return filtered

    def search_nonprofit_all_pages(self, max_pages: int = 10,
                                  fecha_desde: Optional[str] = None,
                                  fecha_hasta: Optional[str] = None) -> List[BDNSConvocatoriaSummary]:
        """
        Search all pages for nonprofit convocatorias

        Args:
            max_pages: Maximum pages to fetch
            fecha_desde: Start date (dd/MM/yyyy)
            fecha_hasta: End date (dd/MM/yyyy)

        Returns:
            List of all nonprofit convocatorias found
        """
        all_results = []
        page = 0

        logger.info(f"🔍 Fetching nonprofit convocatorias (max {max_pages} pages)...")

        while page < max_pages:
            try:
                response = self.search_nonprofit(
                    page=page,
                    page_size=50,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta
                )

                if not response.content:
                    logger.info(f"📄 No more results at page {page}")
                    break

                all_results.extend(response.content)
                logger.info(f"📄 Page {page + 1}: {len(response.content)} results ({len(all_results)}/{response.totalElements} total)")

                # Stop if we've reached the last page
                if response.last or len(all_results) >= response.totalElements:
                    break

                page += 1
                time.sleep(0.5)  # Extra rate limiting for multi-page requests

            except BDNSAPIError as e:
                logger.error(f"❌ Error fetching page {page}: {e}")
                break

        logger.info(f"✅ Total nonprofit convocatorias fetched: {len(all_results)}")
        return all_results

    def get_statistics(self, fecha_desde: Optional[str] = None,
                      fecha_hasta: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about nonprofit convocatorias

        Args:
            fecha_desde: Start date (dd/MM/yyyy)
            fecha_hasta: End date (dd/MM/yyyy)

        Returns:
            Statistics dictionary
        """
        logger.info("📊 Gathering nonprofit statistics...")

        # Get first page to check total
        response = self.search_nonprofit(
            page=0,
            page_size=1,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        stats = {
            'total_nonprofit_convocatorias': response.totalElements,
            'date_range': {
                'desde': fecha_desde or 'No limit',
                'hasta': fecha_hasta or 'Today'
            },
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"📊 Statistics: {response.totalElements} nonprofit convocatorias found")
        return stats


def main():
    """Test the BDNS API client"""
    print("🔧 BDNS API Client Test")
    print("=" * 50)

    # Initialize client
    client = BDNSAPIClient()

    # Test 1: Search nonprofit
    print("\n1️⃣  Searching for nonprofit convocatorias...")
    try:
        response = client.search_nonprofit(page=0, page_size=10)
        print(f"✅ Found {response.totalElements} total nonprofit convocatorias")
        print(f"📄 Showing first {len(response.content)} results:")

        for i, conv in enumerate(response.content[:3], 1):
            print(f"\n   {i}. {conv.numeroConvocatoria}")
            print(f"      📅 {conv.fechaRecepcion}")
            print(f"      🏢 {conv.nivel1}")
            print(f"      📋 {conv.descripcion[:80]}...")

    except BDNSAPIError as e:
        print(f"❌ Error: {e}")

    # Test 2: Get detail
    print("\n2️⃣  Getting detail for first result...")
    try:
        if response.content:
            num_conv = response.content[0].numeroConvocatoria
            detail = client.get_convocatoria_detail(num_conv)

            if detail:
                print(f"✅ Detail retrieved for {num_conv}")
                print(f"   💰 Budget: {detail.presupuestoTotal or 'N/A'} €")
                print(f"   📅 Open: {detail.abierto}")
                if detail.tiposBeneficiarios:
                    print(f"   👥 Beneficiaries: {detail.tiposBeneficiarios[0].descripcion}")

    except BDNSAPIError as e:
        print(f"❌ Error: {e}")

    # Test 3: Statistics
    print("\n3️⃣  Getting statistics...")
    try:
        stats = client.get_statistics()
        print(f"✅ Total nonprofit convocatorias: {stats['total_nonprofit_convocatorias']}")

    except BDNSAPIError as e:
        print(f"❌ Error: {e}")

    print("\n✅ Testing completed!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
