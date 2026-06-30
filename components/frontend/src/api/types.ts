// Result contract — mirrors the backend ResultEnvelope (parent ARCHITECTURE.md §7,
// analyze-agent §9.4). The SPA is a pure renderer of this JSON.

export type Severity = 'low' | 'medium' | 'high';
export type NetAssessment = 'favorable' | 'neutral' | 'unfavorable';
export type ConfidenceLevel = 'low' | 'medium' | 'high';
export type RepoStatus = 'PENDING' | 'READY' | 'FAILED';

export interface TargetNode {
  id: string;
  label: string;
  type: string;
}

export interface Impacted {
  id: string;
  type: string;
  hops: number;
  via: string[];
  severity: Severity;
  domain: string;
  explanation: string;
}

export interface GraphNode {
  id: string;
  label?: string;
  type?: string;
}

export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface WhatBreaks {
  summary: string;
  impacted: Impacted[];
  graph: Graph;
}

export interface Range {
  low: number;
  high: number;
  currency?: string;
  unit?: string;
  basis?: string;
}

export interface LineItem {
  label: string;
  low: number;
  high: number;
  unit: string;
}

export interface WhatItCosts {
  bom_saved: Range;
  eng_rework: Range;
  net_assessment: NetAssessment;
  line_items: LineItem[];
}

export interface RiskItem {
  category: string;
  severity: Severity;
  title: string;
  detail: string;
  revalidation_required: boolean;
}

export interface WhatItRisks {
  items: RiskItem[];
}

export interface Confidence {
  level: ConfidenceLevel;
  model_agreement?: number | null;
}

export interface ResultEnvelope {
  change_request: string;
  target_nodes: TargetNode[];
  what_breaks: WhatBreaks;
  what_it_costs: WhatItCosts;
  what_it_risks: WhatItRisks;
  confidence: Confidence;
}

// API request/response shapes (§6)
export interface IngestResponse {
  repo_id: string;
}

export interface StatusResponse {
  status: RepoStatus;
}

export interface AnalyzeRequest {
  repo_id: string;
  change_request: string;
  session_id?: string;
}

// Input guard verdict. In production this maps to an Amazon Bedrock Guardrail
// (ApplyGuardrail) / lightweight classifier; here it runs as a simple in-app
// pre-check before /analyze.
export interface GuardResult {
  allowed: boolean;
  reason?: string;
  categories?: string[];
}
