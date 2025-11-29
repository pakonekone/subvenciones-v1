"""
PLACSP Service

Service for capturing and processing grants/tenders from PLACSP.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import time

from app.models import Grant
from app.shared.placsp_client import PLACSPClient
from app.shared.codice_parser import CODICEParser
from app.shared.filters import GrantFilter
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class PLACSPService:
    """Service for capturing PLACSP tenders"""

    def __init__(self, db: Session):
        self.db = db
        self.client = PLACSPClient()
        self.parser = CODICEParser()
        self.filter_engine = GrantFilter()
        
    def capture_recent_grants(self, days_back: int = 1, max_pages: int = 10) -> Dict[str, Any]:
        """
        Capture recent tenders from PLACSP feed.
        
        Args:
            days_back: Number of days to look back
            max_pages: Safety limit for pagination
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_fetched": 0,
            "total_nonprofit": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "pages_processed": 0
        }
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        current_url = settings.placsp_feed_url
        
        logger.info(f"🚀 Starting PLACSP capture. Days back: {days_back}, Cutoff: {cutoff_date}")
        
        for page in range(max_pages):
            try:
                logger.info(f"📄 Processing page {page+1}: {current_url}")
                entries, next_link = self.client.fetch_feed(current_url)
                stats["pages_processed"] += 1
                
                if not entries:
                    logger.info("   No entries found on this page.")
                    break
                    
                page_processed_count = 0
                stop_processing = False
                
                for entry in entries:
                    stats["total_fetched"] += 1
                    
                    try:
                        # Parse entry
                        data = self.parser.parse_entry(entry)
                        
                        # Check date (updated)
                        updated_str = data.get('updated')
                        if updated_str:
                            # Parse Atom date format (ISO 8601)
                            # Example: 2023-10-01T12:00:00Z
                            # We need to handle potential format variations
                            try:
                                updated_at = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                                
                                # If entry is older than cutoff, we might want to stop
                                # BUT feeds are not always strictly ordered by updated, so be careful.
                                # However, usually they are ordered new to old.
                                if updated_at < cutoff_date:
                                    logger.debug(f"   Entry {data.get('id')} is older than cutoff ({updated_at}). Stopping.")
                                    stop_processing = True
                                    # We don't break immediately here because there might be mixed dates, 
                                    # but usually we can stop if we see a significant chunk of old dates.
                                    # For safety in this v1, let's just skip this entry but continue page.
                                    # If we want to optimize, we can break if we see consecutive old entries.
                            except ValueError:
                                logger.warning(f"   Could not parse date: {updated_str}")
                        
                        if stop_processing:
                            # If we decided to stop based on date, we skip this entry
                            # In a robust implementation, we might break the loop if we are sure about order.
                            # For now, let's just skip.
                            continue

                        # Filter for Nonprofit
                        # We construct a "grant_info" dict for the filter engine
                        grant_info = {
                            'id': data.get('id'),
                            'title': data.get('title'),
                            'department': data.get('department', ''),
                            'section': '',
                            'epigraph': ''
                        }
                        
                        # Use the 'test_placsp' profile for debugging/broad capture
                        filter_result = self.filter_engine.evaluate_grant(grant_info, 'test_placsp')
                        
                        if filter_result['passed']:
                            stats["total_nonprofit"] += 1
                            confidence = filter_result['total_score']
                            
                            self._save_grant(data, confidence, stats)
                        else:
                            stats["total_skipped"] += 1
                            logger.debug(f"Skipped: {grant_info['title']} (Score: {filter_result['total_score']:.2f})")
                            
                    except Exception as e:
                        logger.error(f"   Error processing entry: {e}")
                        stats["total_errors"] += 1
                
                if stop_processing:
                    logger.info("   Reached cutoff date. Stopping capture.")
                    break
                    
                if not next_link:
                    logger.info("   No next page. Stopping.")
                    break
                    
                current_url = next_link
                # Be nice to the server
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing page {page}: {e}")
                stats["total_errors"] += 1
                break
                
        self.db.commit()
        logger.info(f"✅ PLACSP capture finished. Stats: {stats}")
        return stats

    def _save_grant(self, data: Dict[str, Any], confidence: float, stats: Dict[str, Any]):
        """Save or update grant in database"""
        
        # ID strategy: PLACSP IDs are URLs like https://.../id
        # We want a shorter ID. We can use the last part or the folder_id.
        # Let's use the folder_id if available, prefixed with PLACSP-
        # Or hash the ID URL.
        # For readability, let's try to find a code.
        
        grant_id = data.get('id')
        if not grant_id:
            return

        # Try to make a nice ID
        # Example id: https://contrataciondelestado.es/sindicacion/licitacionesPerfilContratante/123456
        short_id = grant_id.split('/')[-1]
        db_id = f"PLACSP-{short_id}"
        
        # Check if exists
        existing = self.db.query(Grant).filter(Grant.id == db_id).first()
        
        # Parse dates
        pub_date = None
        if data.get('updated'):
            try:
                pub_date = datetime.fromisoformat(data.get('updated').replace('Z', '+00:00'))
            except:
                pass
                
        end_date = None
        if data.get('application_end_date'):
            try:
                # Format from parser might be ISO or simple date
                # Parser returns string.
                # If it has T, it's iso-like
                end_date_str = data.get('application_end_date')
                if 'T' in end_date_str:
                    end_date = datetime.fromisoformat(end_date_str)
                else:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except:
                pass

        if existing:
            # Update
            existing.title = data.get('title') or existing.title
            existing.budget_amount = data.get('budget_amount')
            existing.application_end_date = end_date
            existing.processed_at = datetime.now()
            existing.nonprofit_confidence = confidence
            # Update new fields
            existing.placsp_folder_id = data.get('folder_id')
            existing.contract_type = data.get('contract_type')
            existing.cpv_codes = data.get('cpv_codes')
            existing.regions = data.get('regions')
            existing.pdf_url = data.get('pdf_url')
            existing.html_url = data.get('link')
            if data.get('summary'):
                existing.purpose = data.get('summary')
            
            stats["total_updated"] += 1
        else:
            # Create
            grant = Grant(
                id=db_id,
                source="PLACSP",
                title=data.get('title') or "Sin título",
                department=data.get('department') or "PLACSP",
                publication_date=pub_date,
                captured_at=datetime.now(),
                processed_at=datetime.now(),
                
                # PLACSP specific
                placsp_folder_id=data.get('folder_id'),
                contract_type=data.get('contract_type'),
                cpv_codes=data.get('cpv_codes'),
                
                # Common
                budget_amount=data.get('budget_amount'),
                application_end_date=end_date,
                regions=data.get('regions'),
                pdf_url=data.get('pdf_url'),
                html_url=data.get('link'), # Save official link
                purpose=data.get('summary'), # Save Atom summary as purpose
                
                # Status
                is_open=True, # Assume open if recently captured
                is_nonprofit=True,
                nonprofit_confidence=confidence,
                
                # Default empty for others
                relevance_score=0.0
            )
            self.db.add(grant)
            stats["total_new"] += 1

