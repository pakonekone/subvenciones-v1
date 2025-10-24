#!/usr/bin/env python3
"""
Integración con N8n Webhooks

Este módulo maneja el envío de información de subvenciones del BOE a webhooks de N8n
para su procesamiento con agentes, incluyendo reintentos, formateo de datos y logging.
"""

import os
import sys
import json
import time
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests
import logging


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WebhookPayload:
    """Estructura de datos para envío a N8n"""
    id: str
    source: str = "BOE"
    timestamp: str = ""
    type: str = "grant"
    
    # Información básica
    title: str = ""
    description: str = ""
    department: str = ""
    section: str = ""
    
    # URLs y recursos
    pdf_url: str = ""
    html_url: str = ""
    xml_url: str = ""
    
    # Contenido procesado
    pdf_content_text: str = ""
    pdf_content_markdown: str = ""
    
    # Información extraída
    metadata: Dict[str, Any] = None
    
    # Información de procesamiento
    processing_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
        if self.processing_info is None:
            self.processing_info = {}


class WebhookQueue:
    """Cola de envío de webhooks con persistencia"""
    
    def __init__(self, db_path: str = "webhook_queue.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos SQLite para la cola"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_queue (
                id TEXT PRIMARY KEY,
                webhook_url TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_attempt TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                error_message TEXT,
                success_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON webhook_queue(status);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON webhook_queue(created_at);
        ''')
        
        conn.commit()
        conn.close()
    
    def add_to_queue(self, webhook_url: str, payload: WebhookPayload) -> str:
        """
        Añade un webhook a la cola
        
        Args:
            webhook_url: URL del webhook de N8n
            payload: Datos a enviar
            
        Returns:
            ID del elemento en cola
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        queue_id = str(uuid.uuid4())
        payload_json = json.dumps(asdict(payload), ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO webhook_queue (id, webhook_url, payload)
            VALUES (?, ?, ?)
        ''', (queue_id, webhook_url, payload_json))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📥 Webhook añadido a cola: {queue_id}")
        return queue_id
    
    def get_pending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene elementos pendientes de la cola
        
        Args:
            limit: Máximo número de elementos
            
        Returns:
            Lista de elementos pendientes
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM webhook_queue 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def mark_success(self, queue_id: str):
        """Marca un elemento como enviado exitosamente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE webhook_queue 
            SET status = 'success', success_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (queue_id,))
        
        conn.commit()
        conn.close()
    
    def mark_error(self, queue_id: str, error_message: str):
        """Marca un elemento con error y actualiza intentos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE webhook_queue 
            SET attempts = attempts + 1, 
                last_attempt = CURRENT_TIMESTAMP,
                error_message = ?,
                status = CASE 
                    WHEN attempts >= 4 THEN 'failed'
                    ELSE 'pending'
                END
            WHERE id = ?
        ''', (error_message, queue_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de la cola"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM webhook_queue 
            GROUP BY status
        ''')
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return stats


class N8nWebhookClient:
    """Cliente para envío de webhooks a N8n"""
    
    def __init__(self, webhook_url: str, api_key: Optional[str] = None):
        """
        Inicializa el cliente de webhooks
        
        Args:
            webhook_url: URL del webhook de N8n
            api_key: Clave API opcional para autenticación
        """
        self.webhook_url = webhook_url
        self.api_key = api_key
        self.queue = WebhookQueue()
        
        # Validar URL
        parsed_url = urlparse(webhook_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"URL de webhook inválida: {webhook_url}")
        
        # Configurar sesión HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BOE-N8n-Integration/1.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def _update_analysis_data(self, grant_id: str, analysis_data: Dict[str, Any]):
        """
        Actualiza la base de datos con datos de análisis de N8n
        
        Args:
            grant_id: ID de la subvención
            analysis_data: Datos de análisis devueltos por N8n
        """
        try:
            # Abrir conexión a la base de datos principal
            from boe_to_n8n import load_config
            config = load_config()
            db_path = config.get('db_path', 'boe_processing.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Extraer datos de análisis
            priority = analysis_data.get('priority', '')
            priority_score = analysis_data.get('priority_score', '')
            strategic_value = analysis_data.get('strategic_value', '')
            notification_sent = analysis_data.get('notification_sent', '') == 'true'
            
            # Convertir a números si es posible
            try:
                priority_score = float(priority_score) if priority_score else None
            except (ValueError, TypeError):
                priority_score = None
            
            try:
                strategic_value = float(strategic_value) if strategic_value else None
            except (ValueError, TypeError):
                strategic_value = None
            
            # Actualizar registro
            cursor.execute('''
                UPDATE processed_documents 
                SET priority = ?, 
                    priority_score = ?, 
                    strategic_value = ?, 
                    notification_sent = ?,
                    analysis_timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (priority, priority_score, strategic_value, notification_sent, grant_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Análisis actualizado - {grant_id}: {priority} (score: {priority_score}, valor: {strategic_value})")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos de análisis para {grant_id}: {e}")
    
    def send_grant_data(self, grant_info: Dict[str, Any], 
                       pdf_result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envía información de una subvención a N8n
        
        Args:
            grant_info: Información de la subvención del capturador
            pdf_result: Resultado del procesamiento de PDF (opcional)
            
        Returns:
            True si se envió exitosamente o se añadió a cola
        """
        try:
            # Crear payload estructurado
            payload = self._create_payload(grant_info, pdf_result)
            
            # Intentar envío directo
            if self._send_immediate(payload):
                return True
            
            # Si falla, añadir a cola
            self.queue.add_to_queue(self.webhook_url, payload)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error preparando envío: {e}")
            return False
    
    def _create_payload(self, grant_info: Dict[str, Any],
                       pdf_result: Optional[Dict[str, Any]] = None) -> WebhookPayload:
        """Crea el payload estructurado para N8n"""

        # Detectar si es BDNS
        source = grant_info.get('source', 'BOE')
        section = grant_info.get('section', '')
        grant_id = grant_info.get('id', '')
        is_bdns = source == 'BDNS' or section == 'BDNS' or grant_id.startswith('BDNS-')

        # DEBUG: Log para ver qué está pasando
        if is_bdns:
            logger.info(f"🔍 DEBUG BDNS - ID: {grant_id}")
            logger.info(f"   source={source}, section={section}")
            logger.info(f"   bdns_code={grant_info.get('bdns_code')}")
            logger.info(f"   budget_amount={grant_info.get('budget_amount')}")
            logger.info(f"   application_end_date={grant_info.get('application_end_date')}")

        # Metadatos extraídos del PDF
        extracted_metadata = {}
        pdf_text = ""
        pdf_markdown = ""

        if is_bdns:
            # Para BDNS, crear metadatos estructurados completos
            extracted_metadata = {
                'bdns_code': grant_info.get('bdns_code'),
                'bdns_id': grant_info.get('bdns_id'),
                'budget_amount': grant_info.get('budget_amount'),
                'application_start_date': grant_info.get('application_start_date'),
                'application_end_date': grant_info.get('application_end_date'),
                'is_open': grant_info.get('is_open', False),
                'is_nonprofit': grant_info.get('is_nonprofit', True),
                'nonprofit_confidence': grant_info.get('nonprofit_confidence'),
                'beneficiary_types': grant_info.get('beneficiary_types'),
                'sectors': grant_info.get('sectors'),
                'regions': grant_info.get('regions'),
                'instruments': grant_info.get('instruments'),
                'funds': grant_info.get('funds'),
                'convocatoria_type': grant_info.get('convocatoria_type'),
                'purpose': grant_info.get('purpose'),
                'regulatory_base_url': grant_info.get('regulatory_base_url'),
                'electronic_office': grant_info.get('electronic_office'),
                'state_aid_number': grant_info.get('state_aid_number'),
                'state_aid_url': grant_info.get('state_aid_url')
            }

            # Crear texto descriptivo enriquecido para BDNS
            budget_text = f"{grant_info.get('budget_amount')} EUR" if grant_info.get('budget_amount') else "No especificado"
            open_status = "ABIERTA" if grant_info.get('is_open') else "CERRADA"
            confidence_text = f"{grant_info.get('nonprofit_confidence', 0) * 100:.0f}%" if grant_info.get('nonprofit_confidence') else "No disponible"

            pdf_text = f"""CONVOCATORIA BDNS - {grant_info.get('title', 'Sin título')}
=====================================

INFORMACIÓN GENERAL
-------------------
Código BDNS: {grant_info.get('bdns_code', 'No disponible')}
ID BDNS: {grant_info.get('bdns_id', 'No disponible')}
Organismo: {grant_info.get('department', 'No especificado')}
Tipo: {grant_info.get('convocatoria_type', 'No especificado')}

PRESUPUESTO Y FINANCIACIÓN
--------------------------
Presupuesto Total: {budget_text}
Instrumentos: {grant_info.get('instruments', 'No especificado')}
Fondos: {grant_info.get('funds', 'No especificado')}

PLAZOS Y ESTADO
---------------
Inicio Solicitudes: {grant_info.get('application_start_date', 'No especificado')}
Fin Solicitudes: {grant_info.get('application_end_date', 'No especificado')}
Estado: {open_status}

BENEFICIARIOS Y ALCANCE
-----------------------
Tipos de Beneficiarios: {grant_info.get('beneficiary_types', 'No especificado')}
Sectores: {grant_info.get('sectors', 'No especificado')}
Regiones: {grant_info.get('regions', 'No especificado')}

ORGANIZACIÓN SIN ÁNIMO DE LUCRO
-------------------------------
Dirigida a entidades sin ánimo de lucro: Sí
Confianza del filtro: {confidence_text}

FINALIDAD
---------
{grant_info.get('purpose', 'No especificada')}

INFORMACIÓN NORMATIVA
--------------------
Bases Reguladoras: {grant_info.get('regulatory_base_url', 'No disponible')}
Sede Electrónica: {grant_info.get('electronic_office', 'No disponible')}
Ayuda de Estado: {grant_info.get('state_aid_number', 'No disponible')}
URL Transparencia: {grant_info.get('state_aid_url', 'No disponible')}

DATOS TÉCNICOS
--------------
Fecha de Publicación: {grant_info.get('publication_date', 'No disponible')}
Capturada: {grant_info.get('captured_at', 'No disponible')}
Relevancia Estimada: {grant_info.get('estimated_relevance', 0):.2f}

FUENTE DE DATOS
---------------
Esta convocatoria proviene de la Base de Datos Nacional de Subvenciones (BDNS).
Los datos son estructurados y se actualizan automáticamente desde el sistema oficial.

Para más información:
https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{grant_info.get('bdns_code', '')}
"""

        elif pdf_result and pdf_result.get('success'):
            # Para BOE con PDF procesado
            extracted_info = pdf_result.get('extracted_info', {})
            extracted_metadata = {
                'deadlines': extracted_info.get('deadlines', []),
                'amounts': extracted_info.get('amounts', []),
                'beneficiaries': extracted_info.get('beneficiaries', []),
                'requirements': extracted_info.get('requirements', []),
                'purposes': extracted_info.get('purposes', []),
                'confidence_score': len([v for v in extracted_info.values() if v]) / len(extracted_info) if extracted_info else 0
            }
            pdf_text = pdf_result.get('text', '')[:10000]  # Limitar a 10KB
            pdf_markdown = pdf_result.get('markdown', '')
        
        # Si no hay texto del PDF, crear un fallback con información básica
        if not pdf_text or len(pdf_text.strip()) < 50:
            pdf_text = f"""INFORMACIÓN DE SUBVENCIÓN DEL BOE
=====================================

TÍTULO: {grant_info.get('title', 'Sin título')}

ORGANISMO CONVOCANTE: {grant_info.get('department', 'No especificado')}

SECCIÓN BOE: {grant_info.get('section', '')}

FECHA DE PUBLICACIÓN: {grant_info.get('publication_date', '')}

IDENTIFICADOR: {grant_info.get('id', '')}

ENLACES:
- PDF Original: {grant_info.get('pdf_url', 'No disponible')}
- HTML: {grant_info.get('html_url', 'No disponible')}
- XML: {grant_info.get('xml_url', 'No disponible')}

INFORMACIÓN ADICIONAL:
- Relevancia Estimada: {grant_info.get('estimated_relevance', 0):.2f}
- Sección: {grant_info.get('section', 'No especificada')}

NOTA IMPORTANTE:
El contenido completo del PDF no pudo ser procesado automáticamente.
Para obtener información detallada sobre requisitos, plazos, cuantías y procedimientos,
consulte directamente el documento oficial en el BOE mediante el enlace PDF proporcionado.

Este documento puede contener información sobre:
- Bases reguladoras de la convocatoria
- Requisitos de participación
- Cuantías y presupuestos disponibles
- Plazos de presentación de solicitudes
- Documentación requerida
- Criterios de evaluación
- Procedimientos de concesión"""
        
        # Información de procesamiento
        processing_info = {
            'captured_at': grant_info.get('captured_at'),
            'estimated_relevance': grant_info.get('estimated_relevance', 0),
            'pdf_processed': pdf_result is not None and pdf_result.get('success', False),
            'pdf_size_kb': grant_info.get('pdf_size_kb', 0),
            'extraction_method': 'bdns_api' if is_bdns else ('automatic' if pdf_result else 'metadata_only'),
            'data_type': 'structured' if is_bdns else 'pdf'
        }

        return WebhookPayload(
            id=grant_info.get('id', str(uuid.uuid4())),
            source='BDNS' if is_bdns else 'BOE',
            title=grant_info.get('title', ''),
            description=self._create_description(grant_info),
            department=grant_info.get('department', ''),
            section=grant_info.get('section', ''),
            pdf_url=grant_info.get('pdf_url', ''),
            html_url=grant_info.get('html_url', ''),
            xml_url=grant_info.get('xml_url', ''),
            pdf_content_text=pdf_text,
            pdf_content_markdown=pdf_markdown,
            metadata=extracted_metadata,
            processing_info=processing_info
        )
    
    def _create_description(self, grant_info: Dict[str, Any]) -> str:
        """Crea una descripción breve para la subvención"""
        title = grant_info.get('title', '')
        department = grant_info.get('department', '')
        section = grant_info.get('section', '')
        
        description = f"Convocatoria publicada por {department}"
        if section:
            description += f" en {section}"
        if grant_info.get('estimated_relevance', 0) > 0.5:
            description += " [Alta Relevancia]"
        
        return description
    
    def _send_immediate(self, payload: WebhookPayload) -> bool:
        """
        Intenta envío inmediato del webhook

        Args:
            payload: Datos a enviar

        Returns:
            True si se envió exitosamente
        """
        try:
            logger.info(f"🚀 Enviando webhook a N8n: {payload.title[:60]}...")

            # Convertir payload a dict plano (N8n automáticamente lo envuelve en body)
            # Enviamos directamente los datos sin anidamiento adicional
            payload_dict = asdict(payload)

            response = self.session.post(
                self.webhook_url,
                json=payload_dict,
                timeout=30
            )

            response.raise_for_status()

            # Procesar respuesta de N8n con datos de análisis
            try:
                response_data = response.json()
                if response_data.get('success') and 'data' in response_data:
                    analysis_data = response_data['data']
                    self._update_analysis_data(payload.id, analysis_data)
                    logger.info(f"📊 Datos de análisis guardados para {payload.id}")
            except (ValueError, KeyError) as e:
                logger.warning(f"⚠️  Error procesando respuesta de N8n: {e}")

            logger.info(f"✅ Webhook enviado exitosamente: {payload.id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  Error de red enviando webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando webhook: {e}")
            return False
    
    def process_queue(self, batch_size: int = 5) -> Dict[str, int]:
        """
        Procesa elementos pendientes en la cola
        
        Args:
            batch_size: Número de elementos a procesar
            
        Returns:
            Estadísticas del procesamiento
        """
        stats = {'processed': 0, 'success': 0, 'errors': 0}
        
        pending_items = self.queue.get_pending(batch_size)
        
        if not pending_items:
            logger.info("📭 No hay elementos pendientes en la cola")
            return stats
        
        logger.info(f"🔄 Procesando {len(pending_items)} elementos de la cola...")
        
        for item in pending_items:
            stats['processed'] += 1
            
            try:
                payload_data = json.loads(item['payload'])
                payload = WebhookPayload(**payload_data)
                
                if self._send_immediate(payload):
                    self.queue.mark_success(item['id'])
                    stats['success'] += 1
                else:
                    error_msg = f"Error de red después de {item['attempts']} intentos"
                    self.queue.mark_error(item['id'], error_msg)
                    stats['errors'] += 1
                
                # Pausa entre envíos para no saturar
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error procesando item: {str(e)}"
                self.queue.mark_error(item['id'], error_msg)
                stats['errors'] += 1
                logger.error(f"❌ {error_msg}")
        
        logger.info(f"📊 Procesamiento completado: {stats['success']} éxitos, {stats['errors']} errores")
        return stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene estado de la cola de webhooks"""
        stats = self.queue.get_stats()
        
        return {
            'webhook_url': self.webhook_url,
            'queue_stats': stats,
            'total_items': sum(stats.values()),
            'pending_items': stats.get('pending', 0),
            'success_items': stats.get('success', 0),
            'failed_items': stats.get('failed', 0)
        }
    
    def test_webhook(self) -> bool:
        """
        Envía un mensaje de prueba al webhook
        
        Returns:
            True si el webhook responde correctamente
        """
        test_payload = WebhookPayload(
            id="test-" + str(uuid.uuid4()),
            title="Webhook de prueba BOE",
            description="Este es un mensaje de prueba del sistema BOE",
            type="test",
            metadata={'test': True, 'timestamp': datetime.now().isoformat()}
        )
        
        logger.info("🧪 Enviando mensaje de prueba a N8n...")
        success = self._send_immediate(test_payload)
        
        if success:
            logger.info("✅ Webhook de prueba enviado exitosamente")
        else:
            logger.error("❌ Error enviando webhook de prueba")
        
        return success


def main():
    """Función principal para probar el cliente de webhooks"""
    print("🔗 N8n Webhook Integration - Test")
    print("=" * 40)
    
    # Configuración (en producción vendría de variables de entorno)
    webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://your-n8n.com/webhook/test')
    api_key = os.getenv('N8N_API_KEY')
    
    if webhook_url == 'https://your-n8n.com/webhook/test':
        print("⚠️  Usando URL de webhook de prueba. Configura N8N_WEBHOOK_URL")
    
    try:
        # Crear cliente
        client = N8nWebhookClient(webhook_url, api_key)
        
        # Test de conectividad
        print(f"\n1️⃣  Probando conectividad con N8n...")
        if client.test_webhook():
            print("✅ Webhook funcionando correctamente")
        else:
            print("❌ Webhook no responde - verificar configuración")
        
        # Simular datos de subvención
        print(f"\n2️⃣  Simulando envío de subvención...")
        
        mock_grant = {
            'id': 'BOE-A-2024-TEST',
            'title': 'Ayudas para la digitalización de PYMES - Prueba',
            'department': 'Ministerio de Industria, Comercio y Turismo',
            'section': 'III. Otras disposiciones',
            'pdf_url': 'https://boe.es/test.pdf',
            'html_url': 'https://boe.es/test.html',
            'captured_at': datetime.now().isoformat(),
            'estimated_relevance': 0.8,
            'pdf_size_kb': '245'
        }
        
        mock_pdf_result = {
            'success': True,
            'text': 'Convocatoria de ayudas para PYMES...',
            'markdown': '# Ayudas PYMES\n\nConvocatoria dirigida a pequeñas empresas...',
            'extracted_info': {
                'deadlines': ['30 días desde publicación'],
                'amounts': ['Hasta 10.000 euros por empresa'],
                'beneficiaries': ['Pequeñas y medianas empresas'],
                'requirements': ['Estar dado de alta en el RETA'],
                'purposes': ['Fomentar la digitalización empresarial']
            }
        }
        
        success = client.send_grant_data(mock_grant, mock_pdf_result)
        
        if success:
            print("✅ Datos de subvención enviados")
        else:
            print("❌ Error enviando datos")
        
        # Estado de la cola
        print(f"\n3️⃣  Estado de la cola:")
        status = client.get_queue_status()
        print(f"  📊 Total items: {status['total_items']}")
        print(f"  ⏳ Pendientes: {status['pending_items']}")
        print(f"  ✅ Exitosos: {status['success_items']}")
        print(f"  ❌ Fallidos: {status['failed_items']}")
        
        # Procesar cola si hay elementos pendientes
        if status['pending_items'] > 0:
            print(f"\n4️⃣  Procesando cola...")
            process_stats = client.process_queue()
            print(f"  Procesados: {process_stats['processed']}")
            print(f"  Éxitos: {process_stats['success']}")
            print(f"  Errores: {process_stats['errors']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n💡 Configuración necesaria:")
    print("  export N8N_WEBHOOK_URL='https://your-n8n.com/webhook/boe'")
    print("  export N8N_API_KEY='your_optional_api_key'")


if __name__ == "__main__":
    main()