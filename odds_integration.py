"""
UFC Odds Integration Module
Handles fetching, parsing, and converting bookmaker odds
to implied probabilities with vig removal.
"""
import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketOdds:
    """Represents odds from a bookmaker for a fight"""
    fighter_a: str
    fighter_b: str
    odds_a: float  # Decimal odds
    odds_b: float  # Decimal odds
    source: str    # Bookmaker name
    timestamp: str
    
    @property
    def implied_prob_a(self) -> float:
        """Raw implied probability (before vig removal)"""
        return 1 / self.odds_a if self.odds_a > 0 else 0
    
    @property
    def implied_prob_b(self) -> float:
        """Raw implied probability (before vig removal)"""
        return 1 / self.odds_b if self.odds_b > 0 else 0
    
    @property
    def overround(self) -> float:
        """Bookmaker margin/vig (should be > 1.0)"""
        return self.implied_prob_a + self.implied_prob_b
    
    def get_vig_free_probabilities(self) -> Tuple[float, float]:
        """
        Remove vig by normalizing implied probabilities.
        Returns (market_prob_a, market_prob_b) that sum to 1.0
        """
        raw_a = self.implied_prob_a
        raw_b = self.implied_prob_b
        total = raw_a + raw_b
        
        if total == 0:
            return 0.5, 0.5
        
        # Normalize to remove vig
        market_prob_a = raw_a / total
        market_prob_b = raw_b / total
        
        return market_prob_a, market_prob_b


class OddsConverter:
    """Convert between different odds formats"""
    
    @staticmethod
    def american_to_decimal(american: int) -> float:
        """Convert American odds to decimal"""
        if american > 0:
            return (american / 100) + 1
        else:
            return (100 / abs(american)) + 1
    
    @staticmethod
    def fractional_to_decimal(fractional: str) -> float:
        """Convert fractional odds (e.g., '5/2') to decimal"""
        try:
            num, den = fractional.split('/')
            return (int(num) / int(den)) + 1
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def decimal_to_american(decimal: float) -> int:
        """Convert decimal odds to American"""
        if decimal >= 2.0:
            return int((decimal - 1) * 100)
        else:
            return int(-100 / (decimal - 1))


class OddsManager:
    """Manages odds fetching and storage"""
    
    def __init__(self, cache_file: str = "odds_cache.json"):
        self.cache_file = cache_file
        self.odds_cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cached odds from file"""
        try:
            with open(self.cache_file, 'r') as f:
                self.odds_cache = json.load(f)
        except FileNotFoundError:
            self.odds_cache = {}
    
    def _save_cache(self):
        """Save odds cache to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.odds_cache, f, indent=2)
    
    def get_odds(self, fighter_a: str, fighter_b: str, 
                 event_date: str = None) -> Optional[MarketOdds]:
        """
        Get odds for a fight. Checks cache first, then fetches fresh.
        
        TODO: Implement actual bookmaker API integration
        For now, returns cached odds or None
        """
        fight_key = f"{fighter_a.lower()}_vs_{fighter_b.lower()}"
        
        # Check cache
        if fight_key in self.odds_cache:
            cached = self.odds_cache[fight_key]
            # Check if still fresh (less than 1 hour old)
            cached_time = datetime.fromisoformat(cached['timestamp'])
            if (datetime.now() - cached_time).seconds < 3600:
                return MarketOdds(
                    fighter_a=cached['fighter_a'],
                    fighter_b=cached['fighter_b'],
                    odds_a=cached['odds_a'],
                    odds_b=cached['odds_b'],
                    source=cached['source'],
                    timestamp=cached['timestamp']
                )
        
        # TODO: Fetch from bookmaker API
        # For now, return None - caller should handle missing odds
        return None
    
    def store_odds(self, odds: MarketOdds):
        """Store odds in cache"""
        fight_key = f"{odds.fighter_a.lower()}_vs_{odds.fighter_b.lower()}"
        self.odds_cache[fight_key] = {
            'fighter_a': odds.fighter_a,
            'fighter_b': odds.fighter_b,
            'odds_a': odds.odds_a,
            'odds_b': odds.odds_b,
            'source': odds.source,
            'timestamp': odds.timestamp
        }
        self._save_cache()
    
    def fetch_odds_from_api(self, fighter_a: str, fighter_b: str,
                           bookmaker: str = "ladbrokes") -> Optional[MarketOdds]:
        """
        Fetch odds from bookmaker API.
        
        TODO: Implement actual API calls to:
        - Ladbrokes API
        - Sportsbet API  
        - Bet365 API
        - Odds API (aggregated)
        
        Returns MarketOdds or None if not available
        """
        # Placeholder for actual API implementation
        # This would make HTTP requests to bookmaker APIs
        pass


def calculate_edge(model_prob: float, market_prob: float) -> float:
    """
    Calculate edge between model probability and market probability.
    
    Edge = Model Probability - Market Probability
    
    Positive edge = Model thinks fighter is MORE likely to win than market
    Negative edge = Model thinks fighter is LESS likely to win than market
    
    Examples:
        Model: 63%, Market: 55% → Edge = +8% (value bet)
        Model: 63%, Market: 67% → Edge = -4% (no value)
    """
    return model_prob - market_prob


def get_edge_rating(edge: float) -> str:
    """Get qualitative rating for edge value"""
    if edge >= 0.10:
        return "Strong Value"
    elif edge >= 0.05:
        return "Value"
    elif edge >= 0.02:
        return "Slight Value"
    elif edge >= -0.02:
        return "Fair Price"
    elif edge >= -0.05:
        return "Slight Underlay"
    else:
        return "No Value"


def format_odds_for_display(decimal_odds: float) -> str:
    """Format odds for display (handles both decimal and American)"""
    if decimal_odds <= 0:
        return "N/A"
    
    american = OddsConverter.decimal_to_american(decimal_odds)
    
    if american > 0:
        return f"+{american} ({decimal_odds:.2f})"
    else:
        return f"{american} ({decimal_odds:.2f})"


# Example usage and testing
if __name__ == "__main__":
    # Example: Josh Emmett vs Kevin Vallejos
    # Market odds: Emmett 1.80, Vallejos 2.20
    
    odds = MarketOdds(
        fighter_a="Josh Emmett",
        fighter_b="Kevin Vallejos",
        odds_a=1.80,
        odds_b=2.20,
        source="Ladbrokes",
        timestamp=datetime.now().isoformat()
    )
    
    print("=" * 60)
    print("UFC Odds Integration Demo")
    print("=" * 60)
    print(f"\nFight: {odds.fighter_a} vs {odds.fighter_b}")
    print(f"Source: {odds.source}")
    print(f"\nMarket Odds:")
    print(f"  {odds.fighter_a}: {format_odds_for_display(odds.odds_a)}")
    print(f"  {odds.fighter_b}: {format_odds_for_display(odds.odds_b)}")
    
    print(f"\nImplied Probabilities (with vig):")
    print(f"  {odds.fighter_a}: {odds.implied_prob_a:.1%}")
    print(f"  {odds.fighter_b}: {odds.implied_prob_b:.1%}")
    print(f"  Overround: {odds.overround:.3f} ({(odds.overround-1)*100:.1f}% vig)")
    
    market_a, market_b = odds.get_vig_free_probabilities()
    print(f"\nVig-Free Market Probabilities:")
    print(f"  {odds.fighter_a}: {market_a:.1%}")
    print(f"  {odds.fighter_b}: {market_b:.1%}")
    
    # Example model prediction
    model_prob_a = 0.63  # Model says 63% chance
    edge_a = calculate_edge(model_prob_a, market_a)
    edge_b = calculate_edge(1 - model_prob_a, market_b)
    
    print(f"\nModel vs Market:")
    print(f"  Model probability: {model_prob_a:.1%}")
    print(f"  Market probability: {market_a:.1%}")
    print(f"  Edge: {edge_a:+.1%} ({get_edge_rating(edge_a)})")
