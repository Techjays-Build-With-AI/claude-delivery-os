# SupportCopilot — Technical Specification

**Version:** 0.3 (2026-06-20)

## 1. Overview

SupportCopilot is an AI assistant that helps customer-support agents at Acme draft replies
to customer tickets. When an agent opens a ticket, SupportCopilot retrieves relevant help-center
articles and past resolved tickets, and uses an LLM to draft a suggested reply that the agent can
edit and send. Goal: make agents faster and more consistent.

## 2. Architecture

The system has three parts:

- **Web app** (React) embedded in the Zendesk agent console.
- **Backend API** (Python/FastAPI) that handles requests from the web app.
- **Retrieval service** that searches our knowledge base (help articles + resolved tickets)
  stored in a Postgres database with pgvector.

When an agent clicks "Draft reply", the web app calls the backend, which queries the retrieval
service for relevant context, builds a prompt, calls GPT-4o, and returns the draft to the web app.

We will use OpenAI for the LLM. Embeddings are generated with text-embedding-3-small.

## 3. Features

### 3.1 Draft reply
Agent opens a ticket → clicks "Draft reply" → sees a generated draft → edits → sends.
The backend retrieves the top 5 most similar articles/tickets and includes them in the prompt.

### 3.2 Summarize ticket
For long ticket threads, the agent can click "Summarize" to get a short summary of the conversation.

### 3.3 Tone adjustment
The agent can ask SupportCopilot to make a draft "more formal" or "more friendly".

## 4. Data

We store help articles and resolved tickets with their embeddings in Postgres (pgvector).
Each row has the text content, an embedding vector, and a source link.
Customer ticket data comes from Zendesk via their API.

## 5. API

- `POST /draft` — returns a draft reply for a ticket.
- `POST /summarize` — returns a summary of a ticket thread.
- `POST /tone` — adjusts the tone of a draft.

All endpoints return JSON.

## 6. Libraries

- FastAPI for the backend.
- React for the frontend.
- The OpenAI SDK.
- LangChain for orchestration.
- pgvector for similarity search.

## 7. Infrastructure

The backend runs on AWS. We'll deploy it as a container. Secrets like the OpenAI API key are
stored as environment variables. We'll set up staging and production environments.

## 8. Deployment

We push to the main branch and it deploys automatically via GitHub Actions.
