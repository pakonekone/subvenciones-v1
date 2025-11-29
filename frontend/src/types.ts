export interface Grant {
  id: string
  source: string
  title: string
  department: string | null
  publication_date: string | null
  application_start_date: string | null
  application_end_date: string | null
  budget_amount: number | null
  is_nonprofit: boolean
  is_open: boolean
  sent_to_n8n: boolean
  bdns_code: string | null
  nonprofit_confidence: number | null
  beneficiary_types: string[] | null
  sectors: string[] | null
  regions: string[] | null
  purpose: string | null
  regulatory_base_url: string | null
  electronic_office: string | null
  google_sheets_exported: boolean
  google_sheets_exported_at: string | null
  google_sheets_url: string | null
  html_url?: string | null
  // PLACSP fields
  placsp_folder_id?: string | null
  contract_type?: string | null
  cpv_codes?: string[] | null
  pdf_url?: string | null
}

export interface GrantsResponse {
  total: number
  grants: Grant[]
}
