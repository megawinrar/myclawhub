"""
OpenAI API cost tracking and monitoring.
Tracks token usage, costs, and provides statistics.
"""
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# Pricing per 1K tokens (as of Dec 2024)
# Update these when OpenAI changes pricing
MODEL_PRICING = {
    "gpt-4o": {
        "input": 0.0025,   # $2.50 per 1M input tokens
        "output": 0.010,   # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.00015,  # $0.15 per 1M input tokens
        "output": 0.00060, # $0.60 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 0.010,
        "output": 0.030,
    },
    "gpt-3.5-turbo": {
        "input": 0.0005,
        "output": 0.0015,
    },
}

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class UsageRecord:
    """Single API call usage record."""
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    endpoint: str  # e.g., "classify", "chat", "extract"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "UsageRecord":
        return cls(**data)


class CostTracker:
    """Tracks OpenAI API costs and usage statistics."""
    
    def __init__(self, redis_client=None, prefix: str = "openai:cost"):
        self.redis = redis_client
        self.prefix = prefix
        self.daily_budget: Optional[float] = None
        self.weekly_budget: Optional[float] = None
        self.monthly_budget: Optional[float] = None
        
        # Local cache for non-redis mode
        self._local_cache: List[UsageRecord] = []
    
    def set_budgets(self, daily: float = None, weekly: float = None, monthly: float = None):
        """Set spending budgets for alerts."""
        self.daily_budget = daily
        self.weekly_budget = weekly
        self.monthly_budget = monthly
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for token usage."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING[DEFAULT_MODEL])
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        endpoint: str = "unknown"
    ) -> float:
        """Record API usage and return cost."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        record = UsageRecord(
            timestamp=time.time(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            endpoint=endpoint
        )
        
        # Store in Redis or local cache
        if self.redis:
            self._store_in_redis(record)
        else:
            self._local_cache.append(record)
        
        return cost
    
    def _store_in_redis(self, record: UsageRecord):
        """Store usage record in Redis with time-based keys."""
        dt = datetime.fromtimestamp(record.timestamp)
        
        # Daily key: openai:cost:daily:2024-12-25
        daily_key = f"{self.prefix}:daily:{dt.strftime('%Y-%m-%d')}"
        # Weekly key: openai:cost:weekly:2024-52
        weekly_key = f"{self.prefix}:weekly:{dt.strftime('%Y-%W')}"
        # Monthly key: openai:cost:monthly:2024-12
        monthly_key = f"{self.prefix}:monthly:{dt.strftime('%Y-%m')}"
        
        # Store record in list
        record_json = json.dumps(record.to_dict())
        
        # Add to time-series
        for key in [daily_key, weekly_key, monthly_key]:
            self.redis.lpush(key, record_json)
            self.redis.expire(key, 90 * 24 * 3600)  # 90 days TTL
        
        # Update counters
        self.redis.hincrbyfloat(f"{daily_key}:summary", "total_cost", record.cost_usd)
        self.redis.hincrby(f"{daily_key}:summary", "total_calls", 1)
        self.redis.hincrby(f"{daily_key}:summary", f"model:{record.model}:calls", 1)
        self.redis.hincrbyfloat(f"{daily_key}:summary", f"model:{record.model}:cost", record.cost_usd)
    
    def get_daily_stats(self, date: Optional[str] = None) -> dict:
        """Get usage statistics for a specific day."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if self.redis:
            key = f"{self.prefix}:daily:{date}:summary"
            stats = self.redis.hgetall(key)
            return {
                "date": date,
                "total_cost": float(stats.get("total_cost", 0)),
                "total_calls": int(stats.get("total_calls", 0)),
                "models": {k: v for k, v in stats.items() if k.startswith("model:")}
            }
        else:
            # Calculate from local cache
            day_start = datetime.strptime(date, '%Y-%m-%d').timestamp()
            day_end = day_start + 24 * 3600
            
            day_records = [
                r for r in self._local_cache
                if day_start <= r.timestamp < day_end
            ]
            
            return self._aggregate_records(day_records, date)
    
    def get_weekly_stats(self, year: int = None, week: int = None) -> dict:
        """Get usage statistics for a specific week."""
        if year is None:
            year = datetime.now().year
        if week is None:
            week = int(datetime.now().strftime('%W'))
        
        if self.redis:
            key = f"{self.prefix}:weekly:{year}-{week:02d}:summary"
            # Calculate from daily summaries
            total_cost = 0
            total_calls = 0
            
            # Get all days in this week
            for i in range(7):
                day = datetime.strptime(f"{year}-W{week}-{i+1}", '%Y-W%W-%w')
                day_stats = self.get_daily_stats(day.strftime('%Y-%m-%d'))
                total_cost += day_stats.get('total_cost', 0)
                total_calls += day_stats.get('total_calls', 0)
            
            return {
                "year": year,
                "week": week,
                "total_cost": round(total_cost, 6),
                "total_calls": total_calls
            }
        else:
            # Calculate from local cache
            week_start = datetime.strptime(f"{year}-W{week}-1", '%Y-W%W-%w').timestamp()
            week_end = week_start + 7 * 24 * 3600
            
            week_records = [
                r for r in self._local_cache
                if week_start <= r.timestamp < week_end
            ]
            
            return self._aggregate_records(week_records, f"{year}-W{week:02d}")
    
    def get_monthly_stats(self, year: int = None, month: int = None) -> dict:
        """Get usage statistics for a specific month."""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        month_key = f"{year}-{month:02d}"
        
        if self.redis:
            total_cost = 0
            total_calls = 0
            
            # Sum all days in month
            for day in range(1, 32):
                try:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    datetime.strptime(date_str, '%Y-%m-%d')  # Validate date
                    day_stats = self.get_daily_stats(date_str)
                    total_cost += day_stats.get('total_cost', 0)
                    total_calls += day_stats.get('total_calls', 0)
                except ValueError:
                    break  # Invalid date (e.g., Feb 30)
            
            return {
                "year": year,
                "month": month,
                "total_cost": round(total_cost, 6),
                "total_calls": total_calls
            }
        else:
            # Calculate from local cache
            month_start = datetime(year, month, 1).timestamp()
            if month == 12:
                month_end = datetime(year + 1, 1, 1).timestamp()
            else:
                month_end = datetime(year, month + 1, 1).timestamp()
            
            month_records = [
                r for r in self._local_cache
                if month_start <= r.timestamp < month_end
            ]
            
            return self._aggregate_records(month_records, month_key)
    
    def get_current_period_stats(self) -> dict:
        """Get stats for current day, week, and month."""
        now = datetime.now()
        
        return {
            "today": self.get_daily_stats(),
            "this_week": self.get_weekly_stats(),
            "this_month": self.get_monthly_stats(),
            "budget_status": self._check_budgets()
        }
    
    def _check_budgets(self) -> dict:
        """Check budget usage and return alerts."""
        alerts = {}
        
        if self.daily_budget:
            daily_cost = self.get_daily_stats().get('total_cost', 0)
            daily_pct = (daily_cost / self.daily_budget) * 100
            alerts['daily'] = {
                'budget': self.daily_budget,
                'spent': daily_cost,
                'percent': round(daily_pct, 1),
                'alert': daily_pct > 80
            }
        
        if self.weekly_budget:
            weekly_cost = self.get_weekly_stats().get('total_cost', 0)
            weekly_pct = (weekly_cost / self.weekly_budget) * 100
            alerts['weekly'] = {
                'budget': self.weekly_budget,
                'spent': weekly_cost,
                'percent': round(weekly_pct, 1),
                'alert': weekly_pct > 80
            }
        
        if self.monthly_budget:
            monthly_cost = self.get_monthly_stats().get('total_cost', 0)
            monthly_pct = (monthly_cost / self.monthly_budget) * 100
            alerts['monthly'] = {
                'budget': self.monthly_budget,
                'spent': monthly_cost,
                'percent': round(monthly_pct, 1),
                'alert': monthly_pct > 80
            }
        
        return alerts
    
    def _aggregate_records(self, records: List[UsageRecord], period: str) -> dict:
        """Aggregate list of records into statistics."""
        if not records:
            return {
                "period": period,
                "total_cost": 0.0,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "models": {}
            }
        
        total_cost = sum(r.cost_usd for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        
        # Model breakdown
        models = {}
        for r in records:
            if r.model not in models:
                models[r.model] = {"calls": 0, "cost": 0.0}
            models[r.model]["calls"] += 1
            models[r.model]["cost"] += r.cost_usd
        
        return {
            "period": period,
            "total_cost": round(total_cost, 6),
            "total_calls": len(records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "models": models
        }
    
    def format_report(self, stats: dict) -> str:
        """Format statistics as readable report."""
        lines = ["📊 OpenAI API Usage Report", "=" * 40]
        
        # Today
        today = stats.get('today', {})
        lines.append(f"📅 Today: ${today.get('total_cost', 0):.4f} ({today.get('total_calls', 0)} calls)")
        
        # This week
        week = stats.get('this_week', {})
        lines.append(f"📆 This Week: ${week.get('total_cost', 0):.4f} ({week.get('total_calls', 0)} calls)")
        
        # This month
        month = stats.get('this_month', {})
        lines.append(f"🗓️  This Month: ${month.get('total_cost', 0):.4f} ({month.get('total_calls', 0)} calls)")
        
        # Budget alerts
        budgets = stats.get('budget_status', {})
        if budgets:
            lines.append("\n💰 Budget Status:")
            for period, status in budgets.items():
                emoji = "🚨" if status.get('alert') else "✅"
                lines.append(f"  {emoji} {period.capitalize()}: {status['percent']:.0f}% (${status['spent']:.2f} / ${status['budget']:.2f})")
        
        return "\n".join(lines)
