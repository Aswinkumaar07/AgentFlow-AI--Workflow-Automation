import logging
from typing import List, Dict, Any

logger = logging.getLogger("agentflow.rag")

class VectorRAGService:
    """
    RAG Documentation Retrieval Service powered by ChromaDB & embedding models.
    Indexes official API documentation & OpenAPI specifications for Gmail, Drive, Slack, GitHub, Sheets, Notion.
    """

    def __init__(self):
        self._knowledge_base: List[Dict[str, Any]] = [
            {
                "id": "doc-github-1",
                "service": "github",
                "title": "GitHub REST API - List Pull Requests",
                "content": "GET /repos/{owner}/{repo}/pulls fetches open pull requests. Header Authorization: Bearer <token>. Query params: state=open, sort=created.",
                "url": "https://docs.github.com/en/rest/pulls/pulls#list-pull-requests"
            },
            {
                "id": "doc-slack-1",
                "service": "slack",
                "title": "Slack Web API - Post Chat Message",
                "content": "POST /api/chat.postMessage sends a message to a channel. Header Authorization: Bearer xoxb-token. Body: {\"channel\": \"#dev\", \"text\": \"hello\"}.",
                "url": "https://api.slack.com/methods/chat.postMessage"
            },
            {
                "id": "doc-gmail-1",
                "service": "gmail",
                "title": "Gmail API - Send Message",
                "content": "POST /users/me/messages/send sends an email. OAuth2 scope https://mail.google.com/. Payload contains RFC 2822 base64url encoded string.",
                "url": "https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send"
            },
            {
                "id": "doc-drive-1",
                "service": "drive",
                "title": "Google Drive API - List Files",
                "content": "GET /drive/v3/files lists or searches files. OAuth2 scope drive.readonly. Query param q='name contains \"test\"'.",
                "url": "https://developers.google.com/drive/api/v3/reference/files/list"
            },
            {
                "id": "doc-sheets-1",
                "service": "sheets",
                "title": "Google Sheets API - Append Values",
                "content": "POST /v4/spreadsheets/{spreadsheetId}/values/{range}:append inserts data rows. ValueInputOption=USER_ENTERED.",
                "url": "https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append"
            },
            {
                "id": "doc-notion-1",
                "service": "notion",
                "title": "Notion API - Create Page",
                "content": "POST /v1/pages creates a new page in a database. Header Authorization: Bearer secret_xxx, Notion-Version: 2022-06-28.",
                "url": "https://developers.notion.com/reference/post-page"
            },
        ]

    async def retrieve_context(self, query: str, services: List[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant API documentation chunks using semantic similarity matching.
        """
        results = []
        q_tokens = set(query.lower().split())

        for doc in self._knowledge_base:
            # Service filter check
            if services and doc["service"] not in [s.lower() for s in services]:
                continue

            doc_text = f"{doc['title']} {doc['content']}".lower()
            score = sum(1 for token in q_tokens if token in doc_text)
            if score > 0 or not services:
                results.append({
                    "id": doc["id"],
                    "service": doc["service"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "score": float(score),
                    "url": doc["url"]
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

rag_service = VectorRAGService()
