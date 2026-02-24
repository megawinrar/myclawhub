"""
Content extraction and classification.
Extracts decisions, tasks, deadlines from messages.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class ContentType(Enum):
    DECISION = "decision"
    TASK = "task"
    DEADLINE = "deadline"
    LINK = "link"
    CONTEXT = "context"
    REQUIREMENT = "requirement"
    UNKNOWN = "unknown"


@dataclass
class ExtractedItem:
    content_type: ContentType
    content: str  # Normalized 1-2 line summary
    confidence: float  # 0.0 - 1.0
    raw_text: str
    metadata: dict


# Trigger words for classification (Russian + English)
TRIGGERS = {
    ContentType.DECISION: [
        "решили", "принято", "будем", "договорились", "оговорили",
        "decided", "agreed", "let's", "let us", "conclusion",
    ],
    ContentType.TASK: [
        "сделай", "надо", "нужно", "задача", "todo", "task",
        "do", "make", "create", "implement", "add",
        "прикрути", "внедри", "добавь", "обнови",
    ],
    ContentType.DEADLINE: [
        "к ", "до ", "дедлайн", "срок", "deadline", "by ",
        "пятница", "понедельник", "вторник", "среда", "четверг", "суббота", "воскресенье",
        "tomorrow", "today", "next week", "monday", "friday",
    ],
    ContentType.LINK: [
        "http", "github.com", "gitlab", "docs.", "notion.", "figma.com",
        "ссылка", "репо", "документ", "таблица",
    ],
    ContentType.CONTEXT: [
        "строим", "делаем", "проект", "система", "продукт",
        "building", "project", "system", "product", "we are",
    ],
    ContentType.REQUIREMENT: [
        "требование", "правило", "должно", "нужно поддерживать",
        "requirement", "must", "should", "rule", "support",
    ],
}


class ContentExtractor:
    """Extracts structured content from messages."""
    
    def __init__(self):
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )
        self.date_patterns = [
            r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',  # 25.12.2024 or 12/25/2024
            r'\d{4}-\d{2}-\d{2}',  # 2024-12-25
        ]
    
    def classify(self, text: str) -> List[Tuple[ContentType, float]]:
        """Classify message content types with confidence scores."""
        text_lower = text.lower()
        scores = []
        
        for content_type, triggers in TRIGGERS.items():
            score = 0.0
            for trigger in triggers:
                if trigger.lower() in text_lower:
                    score += 0.3  # Base score per trigger
            
            # Boost for multiple triggers
            if score > 0.6:
                score = min(1.0, score + 0.2)
            
            if score > 0:
                scores.append((content_type, min(1.0, score)))
        
        # Sort by confidence descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
    
    def extract_links(self, text: str) -> List[str]:
        """Extract URLs from text."""
        return self.url_pattern.findall(text)
    
    def extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline/date mentions."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # Check for relative dates
        text_lower = text.lower()
        if any(word in text_lower for word in ["завтра", "tomorrow"]):
            return "tomorrow"
        if any(word in text_lower for word in ["сегодня", "today"]):
            return "today"
        
        return None
    
    def normalize(self, text: str, content_type: ContentType) -> str:
        """Normalize to 1-2 line summary."""
        # Remove extra whitespace
        normalized = " ".join(text.split())
        
        # Truncate to ~150 chars for summary
        if len(normalized) > 150:
            normalized = normalized[:147] + "..."
        
        # Add prefix based on type
        prefixes = {
            ContentType.DECISION: "[Решение] ",
            ContentType.TASK: "[Задача] ",
            ContentType.DEADLINE: "[Срок] ",
            ContentType.LINK: "[Ссылка] ",
            ContentType.CONTEXT: "[Контекст] ",
            ContentType.REQUIREMENT: "[Требование] ",
        }
        
        prefix = prefixes.get(content_type, "")
        return prefix + normalized
    
    def extract(self, text: str) -> List[ExtractedItem]:
        """Main extraction method."""
        items = []
        
        # Get classifications
        classifications = self.classify(text)
        
        if not classifications:
            return items
        
        # Take top classification if confidence >= 0.5
        top_type, top_confidence = classifications[0]
        
        if top_confidence < 0.5:
            return items
        
        metadata = {}
        
        # Extract type-specific data
        if top_type == ContentType.LINK:
            links = self.extract_links(text)
            if links:
                metadata["links"] = links
        
        if top_type in [ContentType.DEADLINE, ContentType.TASK]:
            deadline = self.extract_deadline(text)
            if deadline:
                metadata["deadline"] = deadline
        
        # Create item
        normalized = self.normalize(text, top_type)
        
        item = ExtractedItem(
            content_type=top_type,
            content=normalized,
            confidence=top_confidence,
            raw_text=text,
            metadata=metadata
        )
        items.append(item)
        
        # If task with deadline, also create deadline item
        if top_type == ContentType.TASK and "deadline" in metadata:
            deadline_item = ExtractedItem(
                content_type=ContentType.DEADLINE,
                content=f"[Срок] {metadata['deadline']}: {normalized[9:]}",  # Remove [Задача] prefix
                confidence=top_confidence,
                raw_text=text,
                metadata={"parent_task": True}
            )
            items.append(deadline_item)
        
        return items
