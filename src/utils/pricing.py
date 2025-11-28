from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class ModelUsage:
    """Represents usage metrics for GPT-4o-mini"""
    input_tokens: int
    output_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def calculate_cost(self) -> float:
        """Calculate the cost for this usage"""
        input_cost = (self.input_tokens / 1000000) * 0.00015  # $0.15 per 1M input tokens
        output_cost = (self.output_tokens / 1000000) * 0.0006  # $0.60 per 1M output tokens
        return round(input_cost + output_cost, 6)

class ModelsPricing:
    """Manages pricing and cost calculations for GPT-4o-mini"""
    
    def __init__(self):
        """Initialize pricing tracker"""
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_cost = 0.0
    
    def track_usage(self, input_tokens=0, output_tokens=0):
        """Track usage metrics"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        
        # Calculate cost based on standard pricing
        input_cost = (input_tokens / 1000) * 0.03  # $0.03 per 1K tokens
        output_cost = (output_tokens / 1000) * 0.06  # $0.06 per 1K tokens
        self.total_cost += (input_cost + output_cost)
    
    def get_usage_summary(self):
        """Return summary of usage"""
        return {
            'total_tokens': self.total_tokens,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_cost': self.total_cost
        }

    