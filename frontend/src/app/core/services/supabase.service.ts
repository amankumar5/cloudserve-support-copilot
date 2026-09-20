import { Injectable } from '@angular/core';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable({
  providedIn: 'root'
})
export class SupabaseService {
  private supabase: SupabaseClient | null = null;

  constructor() {
    const supabaseUrl = (window as any).__env?.SUPABASE_URL || 'https://xyzcompany.supabase.co';
    const supabaseKey = (window as any).__env?.SUPABASE_ANON_KEY || 'your-supabase-anon-key';

    try {
      this.supabase = createClient(supabaseUrl, supabaseKey);
    } catch (e) {
      console.warn('Supabase client initialization skipped for frontend:', e);
    }
  }

  async getTickets() {
    if (!this.supabase) return { data: [], error: null };
    return await this.supabase.from('tickets').select('*').order('created_at', { ascending: false });
  }

  async updateTicketStatus(ticketId: string, status: string, aiDraft?: any) {
    if (!this.supabase) return { data: null, error: null };
    return await this.supabase.from('tickets').update({ status, ai_draft: aiDraft }).eq('ticket_id', ticketId);
  }

  async logDecision(ticketId: string, intent: string, confidence: number, action: string) {
    if (!this.supabase) return { data: null, error: null };
    return await this.supabase.from('decision_logs').insert([{
      ticket_id: ticketId,
      intent,
      confidence_score: confidence,
      action_taken: action
    }]);
  }
}
