"""
LLM service - Groq API for legal document analysis.
"""

import time
import json
import re
from typing import Dict, List

import httpx

from app.config import settings


class LLMService:
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model

    async def analyze_document(self, text: str, similar_cases: List[Dict], language: str = "English", depth: str = "standard") -> Dict:
        cases_context = "\n\n".join(
            f"[Case {i+1}] {c.get('case_name', 'Unknown')} ({c.get('citation', 'N/A')}) - "
            f"{c.get('court', 'Court')} ({c.get('year', 'N/A')})\n"
            f"Relevance: {c.get('relevance_score', 0.8)*100:.0f}%\n"
            f"Similarity: {c.get('key_similarity', 'N/A')}\n"
            f"Held: {c.get('held', 'N/A')}"
            for i, c in enumerate(similar_cases)
        )

        depth_instruction = {
            "detailed": "Provide extremely detailed analysis with full legal reasoning.",
            "quick": "Provide a concise brief analysis focusing on key points.",
            "standard": "Provide a balanced, comprehensive analysis.",
        }.get(depth, "Provide a balanced analysis.")

        system_prompt = f"""You are VaakShastra, an expert Indian legal AI assistant.

{depth_instruction}

Respond in {language} language (keep case names and section numbers in English).

Your response MUST be valid JSON:
{{
  "summary": "plain-language summary as a single string",
  "key_facts": "bullet-pointed key facts as a single string",
  "ipc_sections": "applicable sections as a single string",
  "verdict_prediction": "prediction with reasoning as a single string",
  "confidence": 85,
  "reasoning": "legal reasoning as a single string"
}}

IMPORTANT: All values must be STRINGS (not dicts or arrays). confidence must be a number."""

        user_prompt = f"""Analyze this legal document:

--- DOCUMENT ---
{text[:6000]}

--- SIMILAR PAST JUDGMENTS ---
{cases_context}

Provide structured analysis as JSON."""

        start_time = time.time()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"},
                },
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        if response.status_code != 200:
            error_data = response.json()
            raise RuntimeError(
                f"Groq API error {response.status_code}: "
                f"{error_data.get('error', {}).get('message', 'Unknown error')}"
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        tokens_used = data.get("usage", {}).get("total_tokens", 0)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise RuntimeError("Failed to parse LLM response")

        result["processing_time_ms"] = elapsed_ms
        result["tokens_used"] = tokens_used
        result["model_used"] = self.model

        return result

    async def retrieve_similar_cases(self, text: str) -> List[Dict]:
        system_prompt = """You are an Indian legal research assistant. Find 5 similar real Indian court cases.

Return valid JSON:
{
  "cases": [
    {
      "case_name": "Full case name",
      "citation": "Legal citation",
      "court": "Court name",
      "year": 2020,
      "relevance_score": 0.85,
      "key_similarity": "Why similar",
      "held": "What was held",
      "sections_involved": "Key sections"
    }
  ]
}"""

        user_prompt = f"""Find 5 similar Indian court cases:

{text[:5000]}

Return as JSON."""

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1500,
                        "response_format": {"type": "json_object"},
                    },
                )

            if response.status_code != 200:
                return []

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            cases = parsed.get("cases", parsed.get("similar_cases", []))
            if isinstance(cases, list):
                return cases[:5]
        except Exception:
            pass

        return []


llm_service = LLMService()
