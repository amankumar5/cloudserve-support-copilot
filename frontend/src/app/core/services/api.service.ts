import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SourceCitation {
  document_id: string;
  document_name: string;
  page_number: number;
  section?: string;
  element_type: string;
  snippet: string;
  gdrive_url?: string;
  relevance_score?: number;
}

export interface QueryRequest {
  question: string;
  chat_history?: { role: string; content: string }[];
  top_k?: number;
  filter_document_id?: string;
}

export interface QueryResponse {
  question: string;
  answer: string;
  sources: SourceCitation[];
  retrieval_time_ms: number;
  generation_time_ms: number;
  query_intent?: string;
}

export interface Ticket {
  ticket_id: string;
  channel: 'email' | 'chat' | 'api_docs' | 'forum';
  customer_name: string;
  customer_tier: 'Standard' | 'Business' | 'Enterprise';
  subject: string;
  body: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  ai_draft?: QueryResponse;
  confidence_score?: number;
  status: 'pending_review' | 'approved' | 'escalated';
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`);
  }

  queryRAG(req: QueryRequest): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.baseUrl}/query`, req);
  }

  getDocuments(): Observable<any> {
    return this.http.get(`${this.baseUrl}/documents`);
  }

  syncDrive(folderId?: string, forceResync: boolean = false): Observable<any> {
    return this.http.post(`${this.baseUrl}/drive/sync`, {
      folder_id: folderId,
      force_resync: forceResync
    });
  }

  getIngestionStatus(jobId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/ingestion/status/${jobId}`);
  }

  getTickets(): Observable<{ total: number; tickets: Ticket[] }> {
    return this.http.get<{ total: number; tickets: Ticket[] }>(`${this.baseUrl}/tickets`);
  }

  approveTicket(ticketId: string, editedAnswer?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/tickets/${ticketId}/approve`, { edited_answer: editedAnswer });
  }

  escalateTicket(ticketId: string, reason?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/tickets/${ticketId}/escalate`, { reason: reason });
  }

  getMetrics(): Observable<any> {
    return this.http.get(`${this.baseUrl}/metrics`);
  }
}

