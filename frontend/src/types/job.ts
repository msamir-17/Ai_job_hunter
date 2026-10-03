export interface Job {
  id: string;
  source: string;
  external_id?: string | null;
  title: string;
  company: string;
  location?: string | null;
  is_remote: boolean;
  description: string;
  requirements: string[];
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string | null;
  url?: string | null;
  posted_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface IngestionRequest {
  source: 'manual' | 'remotive';
  limit?: number;
  use_cache?: boolean;
}

export interface IngestionResult {
  source: string;
  total_fetched: number;
  new_ingested: number;
  duplicates_skipped: number;
  failed: number;
  timestamp: string;
}
