"""
OpenAI-powered classifier for MemoKeeper.
Provides intelligent content classification beyond keyword matching.
"""
import json
import os
from typing import Optional, List
import openai

from extractor import ContentType, ExtractedItem
from cost_tracker import CostTracker


# System prompt for classification
CLASSIFICATION_PROMPT = """You are a message classifier for a team chat monitoring system.
Analyze the message and extract structured information.

Content types:
- decision: Team agreed on something ("решили", "договорились", "agreed", "decided")
- task: Action item assigned ("сделай", "надо", "todo", "need to", "should")
- deadline: Time constraint mentioned (date, "завтра", "к пятнице", "by Friday")
- link: Contains URL, repo, document reference
- context: Project description or status update
- requirement: Rule or constraint ("должно", "must", "required")
- none: No actionable content

Respond in JSON format:
{
  "content_type": "decision|task|deadline|link|context|requirement|none",
  "confidence": 0.0-1.0,
  "summary": "1-2 sentence summary in Russian",
  "metadata": {
    "deadline": "extracted date or null",
    "links": ["urls found"],
    "assignee": "mentioned person or null"
  }
}

Rules:
- confidence > 0.8: Clear actionable item
- confidence 0.5-0.8: Possibly relevant, needs review  
- confidence < 0.5: Not relevant
- Be concise in summary
- Extract explicit deadlines even in tasks"""


class OpenAIClassifier:
    """Classifies messages using OpenAI API with cost tracking."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", cost_tracker: Optional[CostTracker] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Fallback to rule-based if no API key
        self.enabled = self.client is not None
        
        # Cost tracking
        self.cost_tracker = cost_tracker
    
    def classify(self, text: str) -> Optional[ExtractedItem]:
        """Classify message using OpenAI."""
        if not self.enabled:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_PROMPT},
                    {"role": "user", "content": f"Message: {text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistency
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Track usage if cost tracker is available
            if self.cost_tracker:
                usage = response.usage
                self.cost_tracker.record_usage(
                    model=self.model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    endpoint="classify"
                )
            
            # Map to ContentType
            type_mapping = {
                "decision": ContentType.DECISION,
                "task": ContentType.TASK,
                "deadline": ContentType.DEADLINE,
                "link": ContentType.LINK,
                "context": ContentType.CONTEXT,
                "requirement": ContentType.REQUIREMENT,
                "none": None
            }
            
            content_type = type_mapping.get(result.get("content_type"))
            if content_type is None:
                return None
            
            confidence = result.get("confidence", 0.5)
            if confidence < 0.5:
                return None
            
            # Build ExtractedItem
            summary = result.get("summary", text[:150])
            metadata = result.get("metadata", {})
            
            # Add prefix based on type
            prefixes = {
                ContentType.DECISION: "[Решение] ",
                ContentType.TASK: "[Задача] ",
                ContentType.DEADLINE: "[Срок] ",
                ContentType.LINK: "[Ссылка] ",
                ContentType.CONTEXT: "[Контекст] ",
                ContentType.REQUIREMENT: "[Требование] "
            }
            prefix = prefixes.get(content_type, "")
            
            return ExtractedItem(
                content_type=content_type,
                content=prefix + summary,
                confidence=confidence,
                raw_text=text,
                metadata=metadata
            )
            
        except Exception as e:
            # Log error but don't crash - fallback to rule-based
            print(f"OpenAI classification error: {e}")
            return None
    
    def batch_classify(self, texts: List[str]) -> List[Optional[ExtractedItem]]:
        """Classify multiple messages (for bulk processing)."""
        return [self.classify(text) for text in texts]


class HybridExtractor:
    """Combines rule-based and OpenAI extraction for best results."""
    
    def __init__(self, use_openai: bool = True, openai_threshold: float = 0.7, cost_tracker: Optional[CostTracker] = None):
        from extractor import ContentExtractor
        self.rule_extractor = ContentExtractor()
        self.ai_classifier = OpenAIClassifier(cost_tracker=cost_tracker) if use_openai else None
        self.openai_threshold = openai_threshold
    
    def extract(self, text: str) -> List[ExtractedItem]:
        """Extract using both methods, merge results."""
        items = []
        
        # Always try rule-based first (fast, no API cost)
        rule_items = self.rule_extractor.extract(text)
        items.extend(rule_items)
        
        # If rule-based found something with high confidence, use it
        if any(item.confidence >= 0.8 for item in rule_items):
            return items
        
        # Otherwise try OpenAI for better understanding
        if self.ai_classifier and self.ai_classifier.enabled:
            ai_item = self.ai_classifier.classify(text)
            if ai_item and ai_item.confidence >= self.openai_threshold:
                # Avoid duplicates - check if similar to rule-based
                if not self._is_duplicate(ai_item, rule_items):
                    items.append(ai_item)
        
        return items
    
    def _is_duplicate(self, new_item: ExtractedItem, existing: List[ExtractedItem]) -> bool:
        """Check if AI result duplicates rule-based result."""
        for item in existing:
            if item.content_type == new_item.content_type:
                # Simple similarity check
                return True
        return False
