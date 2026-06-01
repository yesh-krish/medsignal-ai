export interface Drug {
  id: number;
  rxcui: string | null;
  input_name: string;
  normalized_name: string | null;
  synonym: string | null;
  tty: string | null;
}

export interface ReactionCount {
  reaction: string;
  count: number;
}

export interface EventTrends {
  top_reported_reactions: ReactionCount[];
  reports_by_year: Record<string, number>;
  seriousness_breakdown: Record<string, number>;
  sex_breakdown: Record<string, number>;
  total_reports: number;
}

export interface DrugLabel {
  id: number;
  drug_id: number;
  set_id: string | null;
  brand_name: string[] | null;
  generic_name: string[] | null;
  warnings: string[] | null;
  adverse_reactions: string[] | null;
  contraindications: string[] | null;
  indications_and_usage: string[] | null;
  boxed_warning: string[] | null;
}

export interface SafetySummary {
  id: number;
  drug_id: number;
  summary_text: string;
  model_name: string;
  input_length: number;
  output_length: number;
  latency_ms: number;
  disclaimer: string;
  created_at: string;
}
