"""
CODICE Parser

Parser for CODICE XML format used in PLACSP.
Extracts relevant fields for the Grant model.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

class CODICEParser:
    """
    Parser for CODICE XML structures.
    """
    
    NAMESPACES = {
        'atom': 'http://www.w3.org/2005/Atom',
        'cac': 'urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2',
        'cac-place-ext': 'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2',
        'cbc-place-ext': 'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2',
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_entry(self, entry: ET.Element) -> Dict[str, Any]:
        """
        Parse a PLACSP Atom entry and extract grant-like data.
        """
        data = {}
        
        # 1. Basic Atom Fields
        id_elem = entry.find('atom:id', self.NAMESPACES)
        title_elem = entry.find('atom:title', self.NAMESPACES)
        updated_elem = entry.find('atom:updated', self.NAMESPACES)
        # Link - PLACSP doesn't always specify rel="alternate", so just get the first link
        link_elem = entry.find("atom:link", self.NAMESPACES)
        
        data['id'] = id_elem.text if id_elem is not None else None
        data['title'] = title_elem.text if title_elem is not None else None
        data['updated'] = updated_elem.text if updated_elem is not None else None
        data['link'] = link_elem.get('href') if link_elem is not None else None

        # 2. CODICE Fields (ContractFolderStatus)
        # Extract summary from Atom entry if available
        summary_elem = entry.find('atom:summary', self.NAMESPACES)
        if summary_elem is not None and summary_elem.text:
            data['summary'] = summary_elem.text
        
        # Parse ContractFolderStatus (the main content)
        folder_status = entry.find('.//cac-place-ext:ContractFolderStatus', self.NAMESPACES)
        
        if folder_status is not None:
            self._parse_folder_status(folder_status, data)
        else:
            self.logger.debug(f"No ContractFolderStatus found for entry {data.get('id')}")
            
        return data

    def _parse_folder_status(self, folder: ET.Element, data: Dict[str, Any]):
        """Extract data from ContractFolderStatus"""
        
        # ContractFolderID (in cbc namespace)
        folder_id = folder.find('cbc:ContractFolderID', self.NAMESPACES)
        if folder_id is not None:
            data['folder_id'] = folder_id.text

        # 3. Department (LocatedContractingParty)
        # Try multiple paths for department
        party = folder.find('.//cac-place-ext:LocatedContractingParty', self.NAMESPACES)
        if party is not None:
            # Try PartyName/Name
            party_name = party.find('.//cac:PartyName/cbc:Name', self.NAMESPACES)
            if party_name is not None and party_name.text:
                data['department'] = party_name.text
            else:
                # Try Party/PartyName/Name
                party_name = party.find('.//cac:Party//cac:PartyName/cbc:Name', self.NAMESPACES)
                if party_name is not None and party_name.text:
                    data['department'] = party_name.text

        # If still no department, try to extract from summary
        if not data.get('department') and data.get('summary'):
            # Summary format: Id licitación: ...; Órgano de Contratación: ...; Importe: ...
            parts = data['summary'].split(';')
            for part in parts:
                if 'Órgano de Contratación:' in part:
                    data['department'] = part.split(':', 1)[1].strip()
                    break

        # 4. Budget Amount
        # ProcurementProject (Main details)
        # ProcurementProject is in cac
        project = folder.find('.//cac:ProcurementProject', self.NAMESPACES)
        if project is not None:
            # Name (Title)
            name = project.find('cbc:Name', self.NAMESPACES)
            if name is not None:
                data['title'] = name.text
                
            # Budget
            budget = project.find('.//cac:BudgetAmount/cbc:TotalAmount', self.NAMESPACES)
            if budget is not None:
                try:
                    data['budget_amount'] = float(budget.text)
                    data['currency'] = budget.get('currencyID')
                except (ValueError, TypeError):
                    pass
            
            # Type code
            type_code = project.find('cbc:TypeCode', self.NAMESPACES)
            if type_code is not None:
                data['contract_type'] = type_code.text
                
            # CPV Codes
            cpvs = []
            for item in project.findall('.//cac:RequiredCommodityClassification/cbc:ItemClassificationCode', self.NAMESPACES):
                cpvs.append(item.text)
            data['cpv_codes'] = cpvs
            
            # Location
            locations = []
            for loc in project.findall('.//cac:RealizedLocation/cbc:CountrySubentity', self.NAMESPACES):
                locations.append(loc.text)
            data['regions'] = locations
        else:
            self.logger.debug(f"No ProcurementProject found for entry {data.get('id')}")

        # TenderingProcess (Deadlines)
        # TenderingProcess is in cac
        process = folder.find('.//cac:TenderingProcess', self.NAMESPACES)
        if process is not None:
            # TenderSubmissionDeadlinePeriod
            deadline = process.find('.//cac:TenderSubmissionDeadlinePeriod/cbc:EndDate', self.NAMESPACES)
            deadline_time = process.find('.//cac:TenderSubmissionDeadlinePeriod/cbc:EndTime', self.NAMESPACES)
            
            if deadline is not None:
                date_str = deadline.text
                if deadline_time is not None:
                    date_str += f"T{deadline_time.text}"
                data['application_end_date'] = date_str

        # General Document Links (Pliegos)
        # GeneralDocument is in cac-place-ext? No, check XML.
        # XML: <ns1:GeneralDocument> -> ns1 is cac-place-ext
        # Inside: <ns1:GeneralDocumentDocumentReference>
        # Inside: <ns4:Attachment> -> ns4 is cac
        # Inside: <ns4:ExternalReference>
        # Inside: <ns2:URI> -> ns2 is cbc
        
        documents = []
        # Find all Attachment URIs anywhere in folder
        for attachment in folder.findall('.//cac:Attachment//cbc:URI', self.NAMESPACES):
            documents.append(attachment.text)
        
        if documents:
            data['pdf_url'] = documents[0] # Pick first as primary for now
            data['documents'] = documents
