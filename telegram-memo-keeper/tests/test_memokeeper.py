"""
Tests for MemoKeeper core logic.
"""
import pytest
import sys
sys.path.insert(0, 'scripts')

from filters import MessageFilter
from extractor import ContentExtractor, ContentType


class TestMessageFilter:
    def setup_method(self):
        self.filter_engine = MessageFilter()
    
    def test_noise_single_plus(self):
        """Should filter single '+' message."""
        assert self.filter_engine.is_noise("+") == True
        assert self.filter_engine.is_noise("✅") == True
    
    def test_noise_single_ok(self):
        """Should filter 'ок' message."""
        assert self.filter_engine.is_noise("ок") == True
        assert self.filter_engine.is_noise("OK") == True
    
    def test_noise_lol(self):
        """Should filter 'лол' message."""
        assert self.filter_engine.is_noise("лол") == True
    
    def test_not_noise_important(self):
        """Should not filter important message."""
        text = "Решили использовать PostgreSQL для хранения данных"
        assert self.filter_engine.is_noise(text) == False
    
    def test_too_long_message(self):
        """Should detect too long messages."""
        long_text = "a" * 2001
        assert self.filter_engine.is_too_long(long_text) == True
    
    def test_should_process_valid(self):
        """Should process valid message."""
        should, reason = self.filter_engine.should_process("Нужно сделать деплой завтра")
        assert should == True
        assert reason is None


class TestContentExtractor:
    def setup_method(self):
        self.extractor = ContentExtractor()
    
    def test_extract_decision(self):
        """Should extract decision."""
        text = "Решили переходить на новую архитектуру"
        items = self.extractor.extract(text)
        
        assert len(items) > 0
        assert items[0].content_type == ContentType.DECISION
        assert "Решение" in items[0].content
    
    def test_extract_task(self):
        """Should extract task."""
        text = "Надо обновить документацию к релизу"
        items = self.extractor.extract(text)
        
        assert len(items) > 0
        assert items[0].content_type == ContentType.TASK
        assert "Задача" in items[0].content
    
    def test_extract_task_with_deadline(self):
        """Should extract task and deadline."""
        text = "Нужно сделать ревью кода к пятнице"
        items = self.extractor.extract(text)
        
        # Should have task + deadline
        types = [item.content_type for item in items]
        assert ContentType.TASK in types
        assert ContentType.DEADLINE in types or any("пятница" in str(item.metadata) for item in items)
    
    def test_extract_link(self):
        """Should extract link."""
        text = "Вот репозиторий: https://github.com/example/repo"
        items = self.extractor.extract(text)
        
        assert len(items) > 0
        assert items[0].content_type == ContentType.LINK
        assert "github.com" in str(items[0].metadata.get("links", []))
    
    def test_no_extraction_for_noise(self):
        """Should not extract from irrelevant text."""
        text = "Как дела? Что нового?"
        items = self.extractor.extract(text)
        
        assert len(items) == 0
    
    def test_classify_confidence(self):
        """Should return confidence scores."""
        text = "Решили использовать Redis для кэширования"
        classifications = self.extractor.classify(text)
        
        assert len(classifications) > 0
        assert classifications[0][1] > 0  # Has confidence score


class TestIdempotency:
    """Tests for idempotency logic."""
    
    def test_idempotency_key_format(self):
        """Idempotency key should have correct format."""
        chat_id = -1001234567890
        message_id = 12345
        content_type = "decision"
        
        key = f"mem:{chat_id}:{message_id}:{content_type}"
        assert key == "mem:-1001234567890:12345:decision"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
