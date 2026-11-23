export interface Entities {
  dates: string[];
  money: string[];
  percentages: string[];
  emails: string[];
  urls: string[];
  keywords: string[];
  alerts: string[];
}

export interface ScanCreated {
  scan_id: string;
  file_name: string;
  file_type: string;
  total_pages: number;
}

export interface PageEvent {
  type: "page";
  page_number: number;
  total_pages: number;
  label: string;
  text_preview: string;
  entities: Entities;
  progress: number;
}

export interface StatusEvent {
  type: "status";
  message: string;
  provider: string;
  total_pages: number;
}

export interface KpiItem {
  label: string;
  value: string;
  description: string;
}

export interface TableRow {
  page: number;
  kind: string;
  value: string;
  context: string;
}

export interface SummarySection {
  title: string;
  content: string;
}

export interface AuditFinding {
  title: string;
  impact: "alto" | "medio" | "bajo";
  detail: string;
  recommendation: string;
}

export interface ScanReport {
  file_name: string;
  file_type: string;
  total_pages: number;
  generated_at: string;
  provider: string;
  executive_summary: {
    overview: string;
    sections: SummarySection[];
    highlights: string[];
  };
  data_report: {
    kpis: KpiItem[];
    entities: Entities;
    table: TableRow[];
  };
  audit: {
    score: number;
    findings: AuditFinding[];
    strengths: string[];
  };
}

export interface DoneEvent {
  type: "done";
  report: ScanReport;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type StreamEvent = PageEvent | StatusEvent | DoneEvent | ErrorEvent;

export const EMPTY_ENTITIES: Entities = {
  dates: [],
  money: [],
  percentages: [],
  emails: [],
  urls: [],
  keywords: [],
  alerts: [],
};
