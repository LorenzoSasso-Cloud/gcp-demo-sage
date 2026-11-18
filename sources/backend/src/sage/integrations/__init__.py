"""Adapters for external services: Vertex AI (LLM + embeddings), Firestore, Cloud Storage, BigQuery.

Main areas:
- llm: Google Gen AI SDK client, in Vertex AI mode (text generation + embeddings).
- firestore: chunk storage and vector search (find_nearest).
- storage: additional instructions read from Cloud Storage at every request.
- bigquery: best-effort analytics logging of questions (MOCK: application logger only).
"""
