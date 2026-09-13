import re
from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import SourceCitation


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    text: str


class KnowledgeRetriever:
    def __init__(self, knowledge_dir: Path) -> None:
        self._chunks = self._load(knowledge_dir)

    @staticmethod
    def _load(knowledge_dir: Path) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for path in sorted(knowledge_dir.glob("*.md")):
            for raw_chunk in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
                text = raw_chunk.strip()
                if text:
                    chunks.append(KnowledgeChunk(path.name, text))
        return chunks

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]+", value)}

    def search(self, query: str, top_k: int) -> list[SourceCitation]:
        query_tokens = self._tokens(query)
        ranked: list[tuple[int, str, KnowledgeChunk]] = []
        for chunk in self._chunks:
            overlap = len(query_tokens & self._tokens(chunk.text))
            if overlap:
                ranked.append((overlap, chunk.source, chunk))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            SourceCitation(source=chunk.source, snippet=chunk.text[:500])
            for _, _, chunk in ranked[: max(1, top_k)]
        ]
