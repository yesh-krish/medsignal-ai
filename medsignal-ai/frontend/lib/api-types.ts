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

export interface IngestionRun {
  id: number;
  drug_id: number;
  source: string;
  status: "running" | "succeeded" | "failed";
  query: string;
  requested_reports: number;
  fetched_reports: number;
  saved_reaction_rows: number;
  duplicate_reports_skipped: number;
  source_last_updated: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
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

export interface SafetyAlert {
  id: number;
  drug_id: number;
  alert_type: "potential_safety_signal";
  reaction: string;
  baseline_count: number;
  current_count: number;
  percent_change: number;
  message: string;
  created_at: string;
}

export interface SignalResult {
  id: number;
  run_id: number;
  drug_id: number;
  reaction: string;
  target_with_reaction: number;
  target_without_reaction: number;
  comparator_with_reaction: number;
  comparator_without_reaction: number;
  prr: number;
  ror: number;
  ror_ci_lower: number;
  ror_ci_upper: number;
  is_potential_signal: boolean;
  explanation: string;
  created_at: string;
}

export interface SignalAnalysisRun {
  id: number;
  drug_id: number;
  status: "running" | "succeeded" | "failed";
  source: string;
  comparator_scope: string;
  minimum_reports: number;
  prr_threshold: number;
  ror_ci_lower_threshold: number;
  target_total_reports: number;
  comparator_total_reports: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface SignalAnalysis {
  run: SignalAnalysisRun;
  results: SignalResult[];
}

export interface SignalHistoryPoint {
  run_id: number;
  completed_at: string | null;
  prr: number;
  ror: number;
  ror_ci_lower: number;
  ror_ci_upper: number;
  target_with_reaction: number;
  is_potential_signal: boolean;
}

export interface ReactionSignalTimeline {
  reaction: string;
  status: "new" | "continuing" | "resolved" | "below_threshold";
  first_detected_at: string | null;
  latest_prr: number;
  latest_ror: number;
  latest_is_potential_signal: boolean;
  points: SignalHistoryPoint[];
}

export interface SignalTimeline {
  drug_id: number;
  run_count: number;
  reactions: ReactionSignalTimeline[];
}

export interface ComparedDrug {
  drug: Drug;
  trends: EventTrends;
  label: DrugLabel | null;
}

export interface SharedReaction {
  reaction: string;
  left_count: number;
  right_count: number;
  absolute_difference: number;
}

export interface LabelSectionComparison {
  section: string;
  left_available: boolean;
  right_available: boolean;
  left_count: number;
  right_count: number;
}

export interface DrugComparison {
  left: ComparedDrug;
  right: ComparedDrug;
  shared_top_reported_reactions: SharedReaction[];
  label_section_comparison: LabelSectionComparison[];
  disclaimer: string;
}

export interface MedicationListItem {
  id: number;
  medication_list_id: number;
  drug_id: number;
  drug: Drug;
  created_at: string;
}

export interface MedicationList {
  id: number;
  name: string;
  items: MedicationListItem[];
  created_at: string;
  updated_at: string;
}

export interface InteractionDrug {
  rxcui: string;
  name: string;
}

export interface InteractionEvidence {
  source_drug_name: string;
  source_rxcui: string;
  matched_drug_name: string | null;
  matched_rxcui: string | null;
  matched_term: string | null;
  match_type: string;
  label_section: string;
  risk_statement: string | null;
  excerpt: string;
}

export interface PotentialInteraction {
  source: string;
  severity: string | null;
  severity_tier: string | null;
  mechanism: string | null;
  risk_category: string | null;
  description: string;
  drugs: InteractionDrug[];
  explanation: string | null;
  assessment_reason: string | null;
  evidence: InteractionEvidence[] | null;
}

export interface InteractionScreening {
  medication_list_id: number;
  checked_rxcuis: string[];
  interactions: PotentialInteraction[];
  disclaimer: string;
}
