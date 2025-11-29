import unittest
import xml.etree.ElementTree as ET
from app.shared.codice_parser import CODICEParser

class TestCODICEParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = CODICEParser()
        
    def test_parse_entry_basic(self):
        xml_content = """
        <entry xmlns="http://www.w3.org/2005/Atom" 
               xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
               xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
               xmlns:dgpe="http://contrataciondelestado.es/codice/placsp">
            <id>https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/123</id>
            <title>Licitación de Prueba</title>
            <updated>2023-10-01T12:00:00Z</updated>
            <link href="https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&amp;idEvl=123" rel="alternate"/>
            <dgpe:ContractFolderStatus>
                <cbc:ContractFolderID>EXP-2023-001</cbc:ContractFolderID>
                <cac:ProcurementProject>
                    <cbc:Name>Servicio de Limpieza</cbc:Name>
                    <cbc:TypeCode>2</cbc:TypeCode>
                    <cac:BudgetAmount>
                        <cbc:TotalAmount currencyID="EUR">100000.00</cbc:TotalAmount>
                    </cac:BudgetAmount>
                    <cac:RequiredCommodityClassification>
                        <cbc:ItemClassificationCode>90910000</cbc:ItemClassificationCode>
                    </cac:RequiredCommodityClassification>
                    <cac:RealizedLocation>
                        <cbc:CountrySubentity>Madrid</cbc:CountrySubentity>
                    </cac:RealizedLocation>
                </cac:ProcurementProject>
                <cac:TenderingProcess>
                    <cac:TenderSubmissionDeadlinePeriod>
                        <cbc:EndDate>2023-12-31</cbc:EndDate>
                        <cbc:EndTime>14:00:00</cbc:EndTime>
                    </cac:TenderSubmissionDeadlinePeriod>
                </cac:TenderingProcess>
            </dgpe:ContractFolderStatus>
        </entry>
        """
        entry = ET.fromstring(xml_content)
        data = self.parser.parse_entry(entry)
        
        self.assertEqual(data['id'], "https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/123")
        self.assertEqual(data['title'], "Servicio de Limpieza")
        self.assertEqual(data['folder_id'], "EXP-2023-001")
        self.assertEqual(data['budget_amount'], 100000.00)
        self.assertEqual(data['currency'], "EUR")
        self.assertEqual(data['contract_type'], "2")
        self.assertEqual(data['cpv_codes'], ["90910000"])
        self.assertEqual(data['regions'], ["Madrid"])
        self.assertEqual(data['application_end_date'], "2023-12-31T14:00:00")

if __name__ == '__main__':
    unittest.main()
