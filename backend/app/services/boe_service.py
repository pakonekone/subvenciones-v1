"""
BOE Service - Captura de grants desde el Boletín Oficial del Estado

Adaptado del proyecto original para la arquitectura v1.0
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging
import re

from app.shared.boe_api import BOEAPIClient, BOEAPIError
from app.models import Grant
from app.config import get_settings
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)
settings = get_settings()


class BOEService:
    """Servicio para capturar grants del BOE"""

    # Palabras clave para identificar subvenciones/ayudas
    GRANT_KEYWORDS = [
        'subvención', 'subvenciones', 'subvencion',
        'ayuda', 'ayudas', 'ayuda económica', 'ayuda financiera',
        'beca', 'becas',
        'premio', 'premios',
        'convocatoria', 'convocatorias', 'convoca',
        'bases reguladoras', 'bases de la convocatoria',
        'fondos next generation', 'next generation eu', 'ngeu',
        'plan de recuperación', 'prtr',
        'línea de ayuda', 'líneas de ayuda',
        'programa de apoyo', 'programa de ayuda',
        'incentivo', 'incentivos',
        'financiación', 'financiacion', 'cofinanciación',
        'startup', 'pyme', 'pymes', 'microempresa',
        'emprendedor', 'emprendedores', 'emprendimiento',
        'innovación', 'i+d+i', 'investigación', 'desarrollo',
        'transformación digital', 'digitalización',
        'sostenibilidad', 'medioambiente', 'economía circular',
        'transición energética', 'energías renovables'
    ]

    # Secciones relevantes del BOE
    RELEVANT_SECTIONS = [
        'I. Disposiciones generales',
        'III. Otras disposiciones',
        'V.A. Anuncios - Contratación del Sector Público',
        'V.B. Anuncios - Otros anuncios oficiales'
    ]

    def __init__(self, db: Session):
        """
        Inicializa el servicio BOE

        Args:
            db: Sesión de base de datos
        """
        self.db = db
        self.boe_client = BOEAPIClient()
        self.pdf_processor = PDFProcessor() if settings.process_pdfs else None

    def is_grant_related(self, title: str, department: str = "") -> bool:
        """
        Determina si un documento está relacionado con subvenciones/ayudas

        Args:
            title: Título del documento
            department: Departamento u organismo que lo publica

        Returns:
            True si parece estar relacionado con ayudas/subvenciones
        """
        text_to_check = f"{title.lower()} {department.lower()}"

        # Buscar palabras clave
        for keyword in self.GRANT_KEYWORDS:
            if keyword.lower() in text_to_check:
                return True

        # Buscar patrones específicos
        patterns = [
            r'orden\s+\w+\/\d+.*convocatoria',
            r'resolución.*ayuda',
            r'real decreto.*subvención',
            r'programa.*\d+.*millones',
            r'línea.*\d+.*euros',
            r'fondo.*dotado',
        ]

        for pattern in patterns:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return True

        return False

    def calculate_relevance(self, title: str, department: str) -> float:
        """
        Calcula un score de relevancia basado en palabras clave

        Args:
            title: Título del documento
            department: Departamento

        Returns:
            Score entre 0 y 1
        """
        text = f"{title.lower()} {department.lower()}"
        score = 0.0

        # Palabras de alta relevancia
        high_relevance = ['next generation', 'pyme', 'startup', 'emprendedor', 'innovación', 'i+d+i']
        for keyword in high_relevance:
            if keyword in text:
                score += 0.3

        # Palabras de relevancia media
        medium_relevance = ['subvención', 'ayuda', 'convocatoria', 'financiación']
        for keyword in medium_relevance:
            if keyword in text:
                score += 0.2

        # Palabras de relevancia baja
        low_relevance = ['beca', 'premio', 'apoyo']
        for keyword in low_relevance:
            if keyword in text:
                score += 0.1

        return min(score, 1.0)

    def _check_nonprofit(self, title: str, department: str = "") -> tuple[bool, float]:
        """
        Verifica si el grant es para nonprofit basándose en palabras clave

        Args:
            title: Título del documento
            department: Departamento

        Returns:
            (is_nonprofit, confidence_score)
        """
        text = f"{title.lower()} {department.lower()}"

        # Palabras clave que indican nonprofit
        nonprofit_keywords = [
            'sin ánimo de lucro', 'sin animo de lucro',
            'ong', 'organizaciones no gubernamentales',
            'asociación', 'asociaciones',
            'fundación', 'fundaciones',
            'entidades sociales', 'tercer sector',
            'voluntariado', 'acción social'
        ]

        confidence = 0.0
        for keyword in nonprofit_keywords:
            if keyword in text:
                confidence += 0.3

        # Si tiene palabras relacionadas pero no específicas, confianza baja
        related_keywords = ['social', 'cooperación', 'solidaridad']
        for keyword in related_keywords:
            if keyword in text:
                confidence += 0.1

        is_nonprofit = confidence >= 0.3
        confidence = min(confidence, 1.0)

        return is_nonprofit, confidence

    def _process_grant_pdf(self, grant: Grant) -> None:
        """
        Procesa el PDF de un grant y actualiza sus campos

        Args:
            grant: Grant object to update with PDF content
        """
        if not self.pdf_processor or not grant.pdf_url:
            return

        try:
            logger.info(f"Processing PDF for {grant.id}")
            result = self.pdf_processor.process_grant_pdf(grant.pdf_url)

            if result['success']:
                # Update grant with PDF content
                grant.pdf_content_text = result.get('text', '')
                grant.pdf_content_markdown = result.get('markdown', '')
                grant.pdf_processed = True

                # Extract additional information from extracted_info
                extracted = result.get('extracted_info', {})

                # Update deadlines if found
                deadlines = extracted.get('deadlines', [])
                if deadlines:
                    try:
                        # Use the first deadline as application_end_date
                        from dateutil import parser
                        grant.application_end_date = parser.parse(deadlines[0])
                    except Exception as e:
                        logger.warning(f"Could not parse deadline {deadlines[0]}: {e}")

                # Update budget if found
                amounts = extracted.get('amounts', [])
                if amounts and not grant.budget_amount:
                    try:
                        # Try to extract numeric value from first amount
                        import re
                        amount_str = amounts[0]
                        # Extract numbers and convert to float
                        numbers = re.findall(r'[\d,\.]+', amount_str.replace('.', '').replace(',', '.'))
                        if numbers:
                            grant.budget_amount = float(numbers[0])
                    except Exception as e:
                        logger.warning(f"Could not parse amount {amounts[0]}: {e}")

                # Update purpose if found and not set
                purposes = extracted.get('purposes', [])
                if purposes and not grant.purpose:
                    grant.purpose = ' '.join(purposes)

                logger.info(f"Successfully processed PDF for {grant.id}")
            else:
                logger.warning(f"PDF processing failed for {grant.id}: {result.get('error', 'Unknown error')}")
                grant.pdf_processed = False

        except Exception as e:
            logger.error(f"Error processing PDF for {grant.id}: {e}")
            grant.pdf_processed = False

    def _create_grant(self, item_data: Dict[str, Any]) -> Grant:
        """
        Crea un objeto Grant desde datos del BOE

        Args:
            item_data: Datos del item BOE

        Returns:
            Grant object
        """
        item_id = item_data['id']
        title = item_data['title']
        department = item_data['department']
        section = item_data.get('section', '')
        publication_date = datetime.strptime(item_data['publication_date'], '%Y-%m-%d').date()

        is_nonprofit, nonprofit_confidence = self._check_nonprofit(title, department)

        # Generate BOE URLs
        date_str = publication_date
        pdf_url = f"https://boe.es/boe/days/{date_str.year}/{date_str.month:02d}/{date_str.day:02d}/pdfs/{item_id}.pdf"
        html_url = f"https://boe.es/diario_boe/txt.php?id={item_id}"
        xml_url = f"https://boe.es/diario_boe/xml.php?id={item_id}"

        grant = Grant(
            id=f"BOE-{item_id}",
            source="BOE",
            title=title,
            department=department,
            section=section,
            publication_date=publication_date,
            purpose=None,  # Will be extracted from PDF if processed
            budget_amount=None,  # Will be extracted from PDF if processed
            is_nonprofit=is_nonprofit,
            nonprofit_confidence=nonprofit_confidence,
            is_open=True,  # Assume open when captured
            sent_to_n8n=False,
            boe_id=item_id,

            # URLs
            pdf_url=pdf_url,
            html_url=html_url,
            xml_url=xml_url,
            regulatory_base_url=pdf_url,

            # Relevance
            relevance_score=item_data.get('estimated_relevance', 0.0),

            # Timestamps
            captured_at=datetime.now(),
            processed_at=datetime.now(),

            # PDF processing status
            pdf_processed=False,  # Will be updated if PDF is processed later
        )

        return grant

    def _update_grant(self, existing_grant: Grant, item_data: Dict[str, Any]) -> Grant:
        """
        Actualiza un grant existente con nueva información

        Args:
            existing_grant: Grant existente
            item_data: Nuevos datos

        Returns:
            Grant actualizado
        """
        # Actualizar campos que pueden cambiar
        existing_grant.title = item_data['title']
        existing_grant.department = item_data['department']
        existing_grant.captured_at = datetime.now()

        return existing_grant

    def capture_daily_grants(
        self,
        target_date: Optional[date] = None,
        min_relevance: float = 0.3
    ) -> Dict[str, Any]:
        """
        Captura grants del BOE de una fecha específica

        Args:
            target_date: Fecha a procesar (por defecto hoy)
            min_relevance: Relevancia mínima para capturar (0-1)

        Returns:
            Estadísticas de la captura
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"Capturing BOE grants for {target_date}")

        total_new = 0
        total_updated = 0
        total_nonprofit = 0
        total_scanned = 0

        try:
            # Obtener sumario del día
            response = self.boe_client.get_boe_summary(target_date)

            if not response.get('data'):
                logger.warning(f"No summary found for {target_date}")
                return {
                    'total_scanned': 0,
                    'total_new': 0,
                    'total_updated': 0,
                    'total_nonprofit': 0,
                    'target_date': target_date.isoformat()
                }

            summary = response['data']

            # Procesar cada diario
            for diary in summary.get('sumario', {}).get('diario', []):
                # Procesar cada sección
                for section in diary.get('seccion', []):
                    section_name = section.get('nombre', '')

                    # Solo procesar secciones relevantes
                    if not any(rel_section in section_name for rel_section in self.RELEVANT_SECTIONS):
                        continue

                    # Procesar cada departamento
                    for dept in section.get('departamento', []):
                        dept_name = dept.get('nombre', '')

                        # Procesar cada epígrafe
                        for epigraph in dept.get('epigrafe', []):
                            items = epigraph.get('item', [])

                            # Normalizar items
                            if isinstance(items, dict):
                                items = [items]
                            elif not isinstance(items, list):
                                continue

                            # Procesar cada item
                            for item in items:
                                total_scanned += 1
                                title = item.get('titulo', '')
                                item_id = item.get('identificador', '')

                                if not title or not item_id:
                                    continue

                                # Verificar si es relevante para subvenciones
                                if not self.is_grant_related(title, dept_name):
                                    continue

                                # Calcular relevancia (informativo, no excluye)
                                relevance = self.calculate_relevance(title, dept_name)
                                # NOTE: Ya NO filtramos por relevancia mínima
                                # El score se guarda para mostrar en la UI, pero no excluye grants

                                # Preparar datos del grant
                                item_data = {
                                    'id': item_id,
                                    'title': title,
                                    'department': dept_name,
                                    'section': section_name,
                                    'publication_date': target_date.strftime('%Y-%m-%d'),
                                    'estimated_relevance': relevance,
                                }

                                # Verificar si ya existe
                                existing_grant = self.db.query(Grant).filter(
                                    Grant.id == f"BOE-{item_id}"
                                ).first()

                                if existing_grant:
                                    # Actualizar
                                    self._update_grant(existing_grant, item_data)
                                    total_updated += 1
                                    logger.info(f"Updated BOE-{item_id}: {title[:60]}...")
                                else:
                                    # Crear nuevo
                                    grant = self._create_grant(item_data)
                                    self.db.add(grant)

                                    # Process PDF if enabled
                                    if self.pdf_processor:
                                        self._process_grant_pdf(grant)

                                    total_new += 1

                                    if grant.is_nonprofit:
                                        total_nonprofit += 1

                                    logger.info(f"Created BOE-{item_id}: {title[:60]}...")

            # Commit changes
            self.db.commit()

        except BOEAPIError as e:
            logger.error(f"BOE API error: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.db.rollback()
            raise

        return {
            'total_scanned': total_scanned,
            'total_new': total_new,
            'total_updated': total_updated,
            'total_nonprofit': total_nonprofit,
            'target_date': target_date.isoformat()
        }

    def capture_date_range(
        self,
        start_date: date,
        end_date: date,
        min_relevance: float = 0.3
    ) -> Dict[str, Any]:
        """
        Captura grants en un rango de fechas

        Args:
            start_date: Fecha de inicio
            end_date: Fecha final
            min_relevance: Relevancia mínima

        Returns:
            Estadísticas consolidadas
        """
        total_new = 0
        total_updated = 0
        total_nonprofit = 0
        total_scanned = 0

        current_date = start_date
        while current_date <= end_date:
            stats = self.capture_daily_grants(current_date, min_relevance)
            total_scanned += stats['total_scanned']
            total_new += stats['total_new']
            total_updated += stats['total_updated']
            total_nonprofit += stats['total_nonprofit']

            current_date += timedelta(days=1)

        return {
            'total_scanned': total_scanned,
            'total_new': total_new,
            'total_updated': total_updated,
            'total_nonprofit': total_nonprofit,
            'date_range': f"{start_date.isoformat()} to {end_date.isoformat()}"
        }
