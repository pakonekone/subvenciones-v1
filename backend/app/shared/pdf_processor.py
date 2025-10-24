#!/usr/bin/env python3
"""
Procesador de PDFs del BOE

Este script descarga y procesa PDFs del BOE para extraer información estructurada
de convocatorias de subvenciones, incluyendo criterios de elegibilidad, plazos,
cuantías y otra información relevante.
"""

import os
import sys
import re
import json
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import tempfile
from pathlib import Path


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Procesador de PDFs del BOE para extraer información de subvenciones"""
    
    def __init__(self, download_dir: Optional[str] = None):
        """
        Inicializa el procesador de PDFs
        
        Args:
            download_dir: Directorio para descargar PDFs (temporal por defecto)
        """
        if download_dir:
            self.download_dir = Path(download_dir)
            self.download_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.download_dir = Path(tempfile.gettempdir()) / "boe_pdfs"
            self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Patrones para extraer información clave
        self.patterns = {
            'deadline': [
                r'plazo.*solicitud.*(\d{1,2}.*(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre).*\d{4})',
                r'fecha.*límite.*(\d{1,2}/\d{1,2}/\d{4})',
                r'hasta.*(\d{1,2}.*(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre).*\d{4})',
                r'(\d{1,2})\s+días.*publicación',
                r'(\d{1,2})\s+días.*hábiles',
                r'plazo.*(\d{1,2})\s+días'
            ],
            'amount': [
                r'(?:cuantía|importe|dotación).*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)',
                r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*euros?)',
                r'presupuesto.*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)',
                r'máximo.*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)',
                r'hasta.*?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*€)',
                r'millones?\s+de\s+euros'
            ],
            'beneficiaries': [
                r'beneficiarios?[:\s]+([^.]+\.)',
                r'podrán ser beneficiarios[:\s]+([^.]+\.)',
                r'dirigida a[:\s]+([^.]+\.)',
                r'destinatarios?[:\s]+([^.]+\.)',
                r'requisitos.*beneficiarios[:\s]+([^.]+\.)',
                r'pyme[s]?',
                r'autónomos?',
                r'empresas?',
                r'personas? físicas?',
                r'personas? jurídicas?',
                r'entidades? sin ánimo de lucro',
                r'asociaciones?',
                r'fundaciones?',
                r'cooperativas?'
            ],
            'requirements': [
                r'requisitos?[:\s]+([^.]+\.)',
                r'documentación[:\s]+([^.]+\.)',
                r'deberán cumplir[:\s]+([^.]+\.)',
                r'condiciones[:\s]+([^.]+\.)',
                r'criterios de elegibilidad[:\s]+([^.]+\.)'
            ],
            'purpose': [
                r'objeto[:\s]+([^.]+\.)',
                r'finalidad[:\s]+([^.]+\.)',
                r'objetivo[:\s]+([^.]+\.)',
                r'destinado a[:\s]+([^.]+\.)',
                r'con el fin de[:\s]+([^.]+\.)'
            ]
        }
    
    def download_pdf(self, pdf_url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Descarga un PDF desde una URL
        
        Args:
            pdf_url: URL del PDF a descargar
            filename: Nombre de archivo opcional
            
        Returns:
            Ruta al archivo descargado o None si falla
        """
        try:
            if not filename:
                # Generar nombre de archivo desde la URL
                filename = pdf_url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename = f"boe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            filepath = self.download_dir / filename
            
            # Verificar si ya existe
            if filepath.exists():
                logger.info(f"📄 PDF ya existe: {filepath}")
                return str(filepath)
            
            # Descargar PDF
            logger.info(f"⬇️  Descargando PDF: {pdf_url}")
            response = requests.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Guardar a archivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"✅ PDF descargado: {filepath} ({filepath.stat().st_size / 1024:.1f} KB)")
            return str(filepath)
            
        except requests.RequestException as e:
            logger.error(f"❌ Error descargando PDF: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto de un PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        text = ""
        
        # Primero intentar con PyPDF2 (más rápido)
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                logger.info(f"📖 Extrayendo texto de {num_pages} páginas con PyPDF2...")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text
                
        except ImportError:
            logger.warning("PyPDF2 no está instalado")
        except Exception as e:
            logger.warning(f"Error con PyPDF2: {e}")
        
        # Si falla o no hay texto, intentar con pdfplumber
        try:
            import pdfplumber
            
            logger.info(f"📖 Extrayendo texto con pdfplumber...")
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                return text
                
        except ImportError:
            logger.warning("pdfplumber no está instalado")
        except Exception as e:
            logger.warning(f"Error con pdfplumber: {e}")
        
        # Como último recurso, usar OCR con pytesseract
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            logger.info(f"📖 Aplicando OCR al PDF...")
            
            pages = convert_from_path(pdf_path, 200)  # 200 DPI
            for i, page in enumerate(pages):
                logger.info(f"  Procesando página {i+1}/{len(pages)}...")
                page_text = pytesseract.image_to_string(page, lang='spa')
                text += page_text + "\n"
            
        except ImportError:
            logger.error("pytesseract o pdf2image no están instalados")
        except Exception as e:
            logger.error(f"Error con OCR: {e}")
        
        return text
    
    def extract_key_information(self, text: str) -> Dict[str, Any]:
        """
        Extrae información clave del texto del PDF
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            Diccionario con información estructurada
        """
        info = {
            'deadlines': [],
            'amounts': [],
            'beneficiaries': [],
            'requirements': [],
            'purposes': [],
            'raw_extracts': {}
        }
        
        # Normalizar texto
        text_normalized = ' '.join(text.split())
        text_lower = text_normalized.lower()
        
        # Extraer plazos
        for pattern in self.patterns['deadline']:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches[:3]:  # Limitar a 3 coincidencias
                if match not in info['deadlines']:
                    info['deadlines'].append(match)
        
        # Extraer cuantías
        for pattern in self.patterns['amount']:
            matches = re.findall(pattern, text_normalized, re.IGNORECASE)
            for match in matches[:5]:  # Limitar a 5 coincidencias
                if match not in info['amounts']:
                    info['amounts'].append(match)
        
        # Extraer beneficiarios
        for pattern in self.patterns['beneficiaries']:
            matches = re.findall(pattern, text_normalized, re.IGNORECASE)
            for match in matches[:3]:
                if isinstance(match, str) and len(match) > 10:  # Filtrar resultados muy cortos
                    clean_match = match[:200] if len(match) > 200 else match
                    if clean_match not in info['beneficiaries']:
                        info['beneficiaries'].append(clean_match)
        
        # Extraer requisitos
        for pattern in self.patterns['requirements']:
            matches = re.findall(pattern, text_normalized, re.IGNORECASE)
            for match in matches[:3]:
                if isinstance(match, str) and len(match) > 10:
                    clean_match = match[:300] if len(match) > 300 else match
                    if clean_match not in info['requirements']:
                        info['requirements'].append(clean_match)
        
        # Extraer propósito/objeto
        for pattern in self.patterns['purpose']:
            matches = re.findall(pattern, text_normalized, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, str) and len(match) > 10:
                    clean_match = match[:300] if len(match) > 300 else match
                    if clean_match not in info['purposes']:
                        info['purposes'].append(clean_match)
        
        # Extraer secciones importantes del texto
        sections_to_extract = [
            'objeto', 'beneficiarios', 'cuantía', 'plazo', 'requisitos',
            'documentación', 'criterios', 'valoración', 'procedimiento'
        ]
        
        for section in sections_to_extract:
            pattern = rf'{section}[:\s]+((?:[^.]{{1,500}}\.)+)'
            match = re.search(pattern, text_normalized, re.IGNORECASE)
            if match:
                info['raw_extracts'][section] = match.group(1)[:1000]
        
        return info
    
    def convert_to_markdown(self, text: str, metadata: Dict[str, Any], extracted_info: Dict[str, Any]) -> str:
        """
        Convierte el texto y la información extraída a formato Markdown
        
        Args:
            text: Texto original del PDF
            metadata: Metadatos del documento (título, organismo, etc.)
            extracted_info: Información estructurada extraída
            
        Returns:
            Documento en formato Markdown
        """
        markdown = f"""# {metadata.get('title', 'Convocatoria de Subvención')}

## 📋 Información General

- **Organismo**: {metadata.get('department', 'N/A')}
- **Fecha de publicación**: {metadata.get('publication_date', datetime.now().strftime('%Y-%m-%d'))}
- **BOE ID**: {metadata.get('id', 'N/A')}
- **URL PDF**: [{metadata.get('pdf_url', 'N/A')}]({metadata.get('pdf_url', '#')})

## 🎯 Objeto y Finalidad

"""
        
        # Añadir propósitos
        if extracted_info['purposes']:
            for purpose in extracted_info['purposes']:
                markdown += f"- {purpose}\n"
        elif 'objeto' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['objeto'] + "\n"
        else:
            markdown += "*(No se pudo extraer automáticamente el objeto)*\n"
        
        markdown += "\n## 👥 Beneficiarios\n\n"
        
        # Añadir beneficiarios
        if extracted_info['beneficiaries']:
            for beneficiary in extracted_info['beneficiaries']:
                markdown += f"- {beneficiary}\n"
        elif 'beneficiarios' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['beneficiarios'] + "\n"
        else:
            markdown += "*(No se pudo extraer automáticamente los beneficiarios)*\n"
        
        markdown += "\n## 💰 Cuantía\n\n"
        
        # Añadir cuantías
        if extracted_info['amounts']:
            for amount in extracted_info['amounts']:
                markdown += f"- {amount}\n"
        elif 'cuantía' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['cuantía'] + "\n"
        else:
            markdown += "*(No se pudo extraer automáticamente la cuantía)*\n"
        
        markdown += "\n## ⏰ Plazos\n\n"
        
        # Añadir plazos
        if extracted_info['deadlines']:
            for deadline in extracted_info['deadlines']:
                markdown += f"- {deadline}\n"
        elif 'plazo' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['plazo'] + "\n"
        else:
            markdown += "*(No se pudo extraer automáticamente los plazos)*\n"
        
        markdown += "\n## 📄 Requisitos y Documentación\n\n"
        
        # Añadir requisitos
        if extracted_info['requirements']:
            for req in extracted_info['requirements']:
                markdown += f"- {req}\n"
        elif 'requisitos' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['requisitos'] + "\n"
        elif 'documentación' in extracted_info['raw_extracts']:
            markdown += extracted_info['raw_extracts']['documentación'] + "\n"
        else:
            markdown += "*(No se pudo extraer automáticamente los requisitos)*\n"
        
        # Añadir criterios de valoración si existen
        if 'criterios' in extracted_info['raw_extracts'] or 'valoración' in extracted_info['raw_extracts']:
            markdown += "\n## ⚖️ Criterios de Valoración\n\n"
            if 'criterios' in extracted_info['raw_extracts']:
                markdown += extracted_info['raw_extracts']['criterios'] + "\n"
            if 'valoración' in extracted_info['raw_extracts']:
                markdown += extracted_info['raw_extracts']['valoración'] + "\n"
        
        # Añadir extracto del texto original (primeras 2000 caracteres)
        markdown += f"\n## 📝 Extracto del Texto Original\n\n```\n{text[:2000]}...\n```\n"
        
        # Añadir metadata de procesamiento
        markdown += f"""
---

### ℹ️ Información de Procesamiento

- **Fecha de extracción**: {datetime.now().isoformat()}
- **Método de extracción**: Procesamiento automático de PDF
- **Confianza de extracción**: Media (requiere revisión manual)

> ⚠️ **Nota**: Esta información ha sido extraída automáticamente. 
> Se recomienda consultar el documento original para confirmar todos los detalles.
"""
        
        return markdown
    
    def process_grant_pdf(self, pdf_url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa completamente un PDF de subvención
        
        Args:
            pdf_url: URL del PDF a procesar
            metadata: Metadatos del documento (título, organismo, etc.)
            
        Returns:
            Diccionario con toda la información procesada
        """
        result = {
            'success': False,
            'pdf_url': pdf_url,
            'metadata': metadata,
            'text': '',
            'markdown': '',
            'extracted_info': {},
            'error': None
        }
        
        try:
            # Descargar PDF
            pdf_path = self.download_pdf(pdf_url)
            if not pdf_path:
                result['error'] = 'No se pudo descargar el PDF'
                return result
            
            # Extraer texto
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                result['error'] = 'No se pudo extraer texto del PDF'
                return result
            
            result['text'] = text
            
            # Extraer información clave
            extracted_info = self.extract_key_information(text)
            result['extracted_info'] = extracted_info
            
            # Convertir a Markdown
            markdown = self.convert_to_markdown(text, metadata, extracted_info)
            result['markdown'] = markdown
            
            result['success'] = True
            logger.info(f"✅ PDF procesado exitosamente: {metadata.get('title', 'Sin título')[:60]}...")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error procesando PDF: {e}")
        
        return result


def main():
    """Función principal para probar el procesador de PDFs"""
    print("📄 BOE PDF Processor - Procesador de PDFs")
    print("=" * 45)
    
    processor = PDFProcessor()
    
    # PDF de ejemplo para probar (cambiar por uno real)
    test_pdf_url = "https://www.boe.es/boe/dias/2024/03/15/pdfs/BOE-A-2024-5436.pdf"
    
    test_metadata = {
        'title': 'Convocatoria de prueba',
        'department': 'Ministerio de Ejemplo',
        'publication_date': '2024-03-15',
        'id': 'BOE-A-2024-5436',
        'pdf_url': test_pdf_url
    }
    
    print(f"\n🧪 Procesando PDF de prueba...")
    result = processor.process_grant_pdf(test_pdf_url, test_metadata)
    
    if result['success']:
        print(f"✅ Procesamiento exitoso")
        print(f"\n📊 Información extraída:")
        
        info = result['extracted_info']
        print(f"  • Plazos encontrados: {len(info['deadlines'])}")
        print(f"  • Cuantías encontradas: {len(info['amounts'])}")
        print(f"  • Beneficiarios identificados: {len(info['beneficiaries'])}")
        print(f"  • Requisitos extraídos: {len(info['requirements'])}")
        print(f"  • Propósitos identificados: {len(info['purposes'])}")
        
        # Guardar markdown
        markdown_file = "test_grant.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(result['markdown'])
        print(f"\n💾 Markdown guardado en: {markdown_file}")
        
        # Guardar JSON completo
        json_file = "test_grant_processed.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # Serializar solo lo que se puede convertir a JSON
            json_result = {
                'success': result['success'],
                'pdf_url': result['pdf_url'],
                'metadata': result['metadata'],
                'text_length': len(result['text']),
                'markdown_length': len(result['markdown']),
                'extracted_info': result['extracted_info']
            }
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON guardado en: {json_file}")
        
    else:
        print(f"❌ Error: {result['error']}")
    
    print("\n💡 Nota: Para usar este procesador necesitas instalar:")
    print("  pip install PyPDF2 pdfplumber")
    print("  (Opcional) pip install pytesseract pdf2image para OCR")


if __name__ == "__main__":
    main()