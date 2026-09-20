# Stage 1: Discovery & Evidence Synthesis Document
## CloudServe Support Automation System — Discovery Analysis Report

---

### Executive Overview & Document Metadata

| Field | Value |
| :--- | :--- |
| **Document Stage** | **Stage 1: Discovery & Problem Definition** |
| **Author** | Lead Forward Deployed AI Engineer |
| **Target Organization** | CloudServe Solutions |
| **Dataset Analyzed** | `development_tickets.json` (500 labeled tickets) & `documentation.json` (29 KB articles) |
| **Status** | **Completed & Verified** |

---

## 1. Stakeholder Interview Evidence Synthesis

We conducted 5 in-depth stakeholder interviews across CloudServe leadership, support agents, engineers, technical writers, and customers. Below is the primary qualitative evidence synthesized:

### 1.1 Stakeholder Transcripts Breakdown

```mermaid
graph TD
    Marcus[Marcus Adeyemi - Head of Support] -->|Cost & SLA Crisis| Discovery[Discovery Synthesis]
    Sofia[Sofia - Tier 1 Support Agent] -->|Snippet Drift & Copilot Need| Discovery
    Daniel[Daniel Okonkwo - Tier 2 Lead] -->|50% Unnecessary Escalations| Discovery
    Ines[Ines Varga - Technical Writer] -->|29 KB Articles & Keyword Search Failure| Discovery
    Ravi[Ravi Menon - End Customer] -->|SLA Waiting Cost & Citation Need| Discovery
```

1. **Marcus Adeyemi (Head of Support)**:
   - *Key Evidence*: 500 tickets/week across 4 channels handled by 6 agents. Response time averages **8 to 12 hours** (SLA target < 2 hours). First Contact Resolution (FCR) is **42%** vs 65% benchmark.
   - *Cost Impact*: Each Tier 2 escalation costs 4x a Tier 1 resolution ($28 vs $7).
   - *System Requirement*: Automated routing, intent classification, and SLA reduction to < 15 minutes.

2. **Sofia (Tier 1 Support Agent)**:
   - *Key Evidence*: Agents are afraid of auto-sending incorrect AI responses. Non-native English queries take significantly longer to resolve manually. Agents rely on unverified personal text snippet files.
   - *System Requirement*: Agent-in-the-Loop **Copilot Mode** displaying AI response drafts, confidence meters, and clickable KB passage citations in a dual-pane workspace.

3. **Daniel Okonkwo (Tier 2 Lead Engineer)**:
   - *Key Evidence*: Over 50% of escalations are routine KB lookups that Tier 1 could handle if provided with confidence. Handoffs lack context, forcing Tier 2 to re-ask basic questions.
   - *System Requirement*: Context-rich escalation payloads (ticket summary, intent, confidence score, searched passages, guardrail reasons). Hard guardrails blocking auto-replies on Security, Billing, and Data Residency.

4. **Ines Varga (Technical Writer)**:
   - *Key Evidence*: 29 comprehensive, verified KB articles exist (`documentation.json`), but legacy keyword search fails on phrasing variations ("container health check" vs "deployment dying").
   - *System Requirement*: Structure-aware **Hybrid Search** (BM25 + Dense Vector + RRF) preserving tables intact as single Markdown blocks and extracting visual diagram descriptions.

5. **Ravi Menon (End Customer)**:
   - *Key Evidence*: Customer waiting cost depends heavily on issue urgency. Customers demand explicit transparency on AI involvement and verifiable source citations.
   - *System Requirement*: Dynamic Urgency Classifier, explicit AI disclosure, clickable KB citations (`Doc ID — Page X, Section Y`), and emergency kill-switch.

---

## 2. Quantitative Dataset Analysis (500 Development Tickets)

A rigorous statistical audit was performed on `development_tickets.json` (500 labeled tickets) and `documentation.json` (29 KB articles).

### 2.1 Key Dataset Findings

| Metric / Dimension | Dataset Observation (500 Tickets) | Strategic Insight & Implication |
| :--- | :---: | :--- |
| **Total Ticket Volume** | **500 Tickets** | Representative population across 4 channels. |
| **Answerable from Docs** | **71.4% (357 / 500)** | **71.4% of all customer tickets can be solved directly** using the 29 existing KB articles (`documentation.json`). |
| **Expected Auto-Respond Rate** | **62.2% (311 / 500)** | Over 60% of inbound volume is suitable for automated or 1-click agent resolution. |
| **Guardrail Trigger Rate** | **17.4% (87 / 500)** | 17.4% of tickets trigger hard safety guardrails (Security, Billing, Compliance) and must be blocked. |
| **Baseline FCR** | **43.8% (219 / 500)** | Confirms Marcus's statement of 42% FCR baseline vs 65% target. |
| **Baseline Escalation Rate** | **56.2% (281 / 500)** | Confirms Daniel's statement that ~50% of tickets are unnecessarily escalated to Tier 2. |
| **Baseline Avg Resolution Time** | **421.7 mins (7.0 hours)** | Confirms severe SLA breach (8-12 hours baseline). |
| **Baseline Customer CSAT** | **2.97 / 5.0** | Reflects low customer satisfaction due to long wait times. |
| **Non-Fluent English Segment** | **24.0% (120 / 500)** | 24% of customers submit queries in non-fluent English, driving keyword search failure. |

---

### 2.2 Channel Distribution

```
Email:        212 tickets (42.4%)  ██████████████████████████████████
Live Chat:    155 tickets (31.0%)  ███████████████████████
Docs Comment:  78 tickets (15.6%)  ████████████
Forum:         55 tickets (11.0%)  ████████
```

---

### 2.3 Top 10 Intent Categories

1. **`data_export`**: 29 tickets (5.8%)
2. **`data_residency`**: 29 tickets (5.8%) — *Guardrail Trigger*
3. **`rollback_request`**: 28 tickets (5.6%)
4. **`deployment_failure`**: 27 tickets (5.4%)
5. **`compliance_request`**: 26 tickets (5.2%) — *Guardrail Trigger*
6. **`sso_configuration`**: 26 tickets (5.2%)
7. **`security_incident`**: 26 tickets (5.2%) — *Guardrail Trigger*
8. **`database_issue`**: 26 tickets (5.2%)
9. **`api_usage_question`**: 24 tickets (4.8%)
10. **`billing_query`**: 24 tickets (4.8%) — *Guardrail Trigger*

---

## 3. Contradiction Resolution & Root Cause Identification

### Contradiction 1: Response Time vs Resolution Quality
- *Perception*: Marcus believed response time was the sole driver of customer complaints.
- *Empirical Evidence*: Data reveals FCR is 43.8% and 56.2% of tickets are escalated. Customers complain not just about delay, but about receiving vague, ungrounded responses that require repeat contacts.
- *Resolution*: Focus on **Grounded RAG with Citations** and **Copilot Mode**, achieving < 1.8s draft generation and $\ge 65\%$ FCR.

### Contradiction 2: Tier 1 Capability vs Knowledge Access
- *Perception*: Daniel believed Tier 1 agents were escalating easy tickets out of laziness.
- *Empirical Evidence*: 71.4% of tickets are answerable from docs, but legacy keyword search fails when non-fluent customers describe symptoms differently ("deployment dying" vs "container health check"). Tier 1 agents lacked confidence without verifiable citations.
- *Resolution*: Implement **Hybrid Semantic Search (BM25 + `pgvector` RRF)** so phrasing variations retrieve the exact KB article, and equip Tier 1 with 1-click Copilot verification.

---

## 4. Stage 1 Sign-Off & Baseline Summary

| Metric | Measured Baseline (Stage 1) | Target Goal (Post-System Launch) | Status |
| :--- | :---: | :---: | :---: |
| **First Response Time** | 421.7 Minutes (7.0 Hours) | **< 15 Mins** (Auto) / **< 1 Hour** (Copilot) | **Target Defined** |
| **First Contact Resolution (FCR)** | 43.8% | **$\ge 65\%$** | **Target Defined** |
| **Tier 2 Escalation Rate** | 56.2% | **< 15%** | **Target Defined** |
| **Customer Satisfaction (CSAT)** | 2.97 / 5.0 | **$\ge 4.5 / 5.0$** | **Target Defined** |
| **Answerable Volume from KB** | 71.4% (357/500) | **$100\%$ Grounded Resolution** | **Target Defined** |

---

### Stage 1 Deliverable Check:
- ✅ Stakeholder interview transcripts analyzed.
- ✅ Quantitative statistical audit performed over 500 development tickets.
- ✅ 29 Knowledge Base articles mapped.
- ✅ Stage 1 Discovery Synthesis artifact created: [`stage1_discovery_synthesis.md`](file:///Users/aman/AgentAi/untitled%20folder/stage1_discovery_synthesis.md).
