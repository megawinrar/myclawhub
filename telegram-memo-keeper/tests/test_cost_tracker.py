"""
Tests for cost tracking.
"""
import pytest
import sys
sys.path.insert(0, 'scripts')

from cost_tracker import CostTracker, UsageRecord, MODEL_PRICING


class TestCostTracker:
    def test_calculate_cost_gpt4o_mini(self):
        """Should calculate cost correctly for gpt-4o-mini."""
        tracker = CostTracker()
        
        # 1000 input + 500 output tokens
        cost = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
        
        # Expected: (1000/1000 * 0.00015) + (500/1000 * 0.00060)
        # = 0.00015 + 0.00030 = 0.00045
        expected = 0.00015 + 0.00030
        assert cost == pytest.approx(expected, rel=1e-5)
    
    def test_calculate_cost_unknown_model(self):
        """Should use default pricing for unknown model."""
        tracker = CostTracker()
        cost = tracker.calculate_cost("unknown-model", 1000, 500)
        
        # Should use gpt-4o-mini pricing
        expected = tracker.calculate_cost("gpt-4o-mini", 1000, 500)
        assert cost == expected
    
    def test_local_cache_storage(self):
        """Should store records in local cache when no Redis."""
        tracker = CostTracker(redis_client=None)
        
        tracker.record_usage("gpt-4o-mini", 100, 50, "test")
        
        assert len(tracker._local_cache) == 1
        assert tracker._local_cache[0].model == "gpt-4o-mini"
    
    def test_daily_stats_empty(self):
        """Should return zero stats for empty period."""
        tracker = CostTracker(redis_client=None)
        
        stats = tracker.get_daily_stats("2024-12-25")
        
        assert stats['total_cost'] == 0.0
        assert stats['total_calls'] == 0
    
    def test_daily_stats_with_records(self):
        """Should aggregate daily stats correctly."""
        tracker = CostTracker(redis_client=None)
        
        # Add some records
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Manually add records to cache
        tracker._local_cache.append(
            UsageRecord(
                timestamp=datetime.now().timestamp(),
                model="gpt-4o-mini",
                input_tokens=1000,
                output_tokens=500,
                cost_usd=0.00045,
                endpoint="test"
            )
        )
        
        stats = tracker.get_daily_stats(today)
        
        assert stats['total_cost'] == 0.00045
        assert stats['total_calls'] == 1
        assert stats['total_input_tokens'] == 1000
        assert stats['total_output_tokens'] == 500
    
    def test_budget_checking(self):
        """Should check budget and create alerts."""
        tracker = CostTracker(redis_client=None)
        tracker.set_budgets(daily=1.0)
        
        # Add record
        tracker.record_usage("gpt-4o-mini", 1000000, 0, "test")  # ~$0.15
        
        stats = tracker.get_current_period_stats()
        budgets = stats['budget_status']
        
        assert 'daily' in budgets
        assert budgets['daily']['budget'] == 1.0
        assert budgets['daily']['percent'] < 20  # Should be around 15%
    
    def test_model_breakdown(self):
        """Should break down stats by model."""
        tracker = CostTracker(redis_client=None)
        
        tracker.record_usage("gpt-4o-mini", 1000, 500, "test")
        tracker.record_usage("gpt-4o", 1000, 500, "test")
        
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        stats = tracker.get_daily_stats(today)
        
        assert 'gpt-4o-mini' in stats['models']
        assert 'gpt-4o' in stats['models']


class TestPricingConstants:
    def test_pricing_structure(self):
        """Should have input and output pricing for each model."""
        for model, pricing in MODEL_PRICING.items():
            assert 'input' in pricing
            assert 'output' in pricing
            assert pricing['input'] > 0
            assert pricing['output'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
