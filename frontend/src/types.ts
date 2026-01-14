// Match Score for organization-grant compatibility
export interface MatchScoreBreakdown {
  beneficiary_type: number
  sectors: number
  regions: number
  budget: number
}

export interface MatchScore {
  total_score: number
  breakdown: MatchScoreBreakdown
  recommendation: "APLICAR" | "REVISAR" | "NO RECOMENDADO"
}

// BDNS Document types
export interface BDNSDocument {
  id: number
  nombre: string
  url: string
  descripcion: string | null
  size: number | null
}

export interface BDNSDocumentContent {
  doc_id: number
  filename: string
  success: boolean
  text: string | null
  error: string | null
}

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
  // BDNS Documents
  bdns_documents?: BDNSDocument[] | null
  bdns_documents_processed?: boolean
  bdns_documents_processed_at?: string | null
  // Match score (calculated dynamically based on organization profile)
  match_score?: MatchScore | null
}

export interface GrantsResponse {
  total: number
  grants: Grant[]
}

// Organization Profile types
export interface OrganizationProfile {
  id: string
  user_id: string
  name: string
  cif: string | null
  organization_type: string | null
  sectors: string[]
  regions: string[]
  annual_budget: number | null
  employee_count: number | null
  founding_year: number | null
  capabilities: string[]
  description: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ProfileOption {
  value: string
  label: string
}

export interface ProfileOptions {
  organization_types: ProfileOption[]
  sectors: ProfileOption[]
  regions: ProfileOption[]
  capabilities: ProfileOption[]
}
