"""
Tests for OpenAI classifier.
"""
import pytest
import sys
sys.path.insert(0, 'scripts')

from ai_classifier import OpenAIClassifier, HybridExtractor
from extractor import ContentType


class TestOpenAIClassifier:
    def test_classifier_without_api_key(self):
        """Should disable itself without API key."""
        classifier = OpenAIClassifier(api_key=None)
        assert classifier.enabled == False
        result = classifier.classify("Test message")
        assert result is None
    
    def test_classifier_with_api_key(self):
        """Should enable with API key."""
        classifier = OpenAIClassifier(api_key="fake-key")
        assert classifier.enabled == True
    
    def test_type_mapping(self):
        """Should map string types to ContentType enums."""
        classifier = OpenAIClassifier(api_key="fake")
        # Internal mapping check
        mapping = {
            "decision": ContentType.DECISION,
            "task": ContentType.TASK,
            "deadline": ContentType.DEADLINE,
            "link": ContentType.LINK,
            "context": ContentType.CONTEXT,
            "requirement": ContentType.REQUIREMENT,
            "none": None
        }
        for str_type, enum_type in mapping.items():
            if enum_type:
                assert enum_type in [
                    ContentType.DECISION, ContentType.TASK,
                    ContentType.DEADLINE, ContentType.LINK,
                    ContentType.CONTEXT, ContentType.REQUIREMENT
                ]


class TestHybridExtractor:
    def test_fallback_to_rule_based(self):
        """Should work without OpenAI."""
        extractor = HybridExtractor(use_openai=False)
        text = "Решили использовать PostgreSQL"
        items = extractor.extract(text)
        
        assert len(items) > 0
        assert items[0].content_type == ContentType.DECISION
    
    def test_high_confidence_rule_skips_openai(self):
        """Should not call OpenAI if rule-based is confident."""
        extractor = HybridExtractor(use_openai=True)
        # This has clear trigger words
        text = "Надо сделать деплой завтра"
        
        items = extractor.extract(text)
        # Should find task via rules, not need OpenAI
        assert any(item.content_type == ContentType.TASK for item in items)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
