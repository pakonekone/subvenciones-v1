# Implementation Plan - PLACSP Integration

Integration of the Public Sector Contracting Platform (PLACSP) as a new data source for grants and tenders.

## User Review Required
> [!IMPORTANT]
> **Data Volume Strategy**: PLACSP feeds are large. We will implement a "days back" strategy similar to BOE to limit the initial fetch.
> **Nonprofit Filtering**: We will reuse the existing nonprofit keyword filtering logic. This might need tuning for tender descriptions.

## Proposed Changes

### Backend

#### [NEW] [placsp_client.py](file:///Users/franconejosmengo/Projects/subvenciones-v1/backend/app/shared/placsp_client.py)
- Client to handle Atom feed connection, pagination, and XML fetching.
- Methods: `fetch_feed`, `get_entry_details`.

#### [NEW] [codice_parser.py](file:///Users/franconejosmengo/Projects/subvenciones-v1/backend/app/shared/codice_parser.py)
- Parser for CODICE XML format.
- Extracts: Title, Amount, Deadlines, Documents, CPV, Location.

#### [NEW] [placsp_service.py](file:///Users/franconejosmengo/Projects/subvenciones-v1/backend/app/services/placsp_service.py)
- Service layer to orchestrate capture.
- Logic: Fetch Feed -> Parse -> Filter (Nonprofit) -> Save to DB.

#### [MODIFY] [capture.py](file:///Users/franconejosmengo/Projects/subvenciones-v1/backend/app/api/v1/capture.py)
- Add endpoint `POST /api/v1/capture/placsp`.

### Frontend

#### [MODIFY] [CaptureConfigDialog.tsx](file:///Users/franconejosmengo/Projects/subvenciones-v1/frontend/src/components/CaptureConfigDialog.tsx)
- Add new tab for "PLACSP".
- Add form for "Days Back" configuration.

#### [MODIFY] [bdns_api.py](file:///Users/franconejosmengo/Projects/subvenciones-v1/backend/app/shared/bdns_api.py)
- (Check if we need to refactor shared filter logic to be more generic, currently in `bdns_service.py`).

## Verification Plan

### Automated Tests
- Unit tests for `CODICEParser` using sample XMLs.
- Integration test for `PLACSPService` (mocking the API).

### Manual Verification
1. Open "Capturar Subvenciones".
2. Select "PLACSP" tab.
3. Run capture for last 1 day.
4. Verify new rows appear in Grants Table with source "PLACSP".
5. Verify PDF links work.
