"""
Base Domain - Abstract base class for all transformation domains.

Defines the contract that all transformation domains must implement
to work with the universal transformation engine.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class ComplexityAssessment:
    """Technical complexity assessment results."""
    overall_score: float  # 1-10 scale
    technical_complexity: float
    business_disruption: float
    resource_requirements: float
    timeline_estimate_weeks: float
    risk_factors: List[str]
    success_probability: float


@dataclass 
class BenefitModel:
    """Business benefit calculation results."""
    annual_cost_savings: float
    annual_revenue_gains: float
    productivity_improvements: float
    risk_mitigation_value: float
    total_annual_benefits: float
    confidence_level: float


@dataclass
class ImplementationStrategy:
    """Implementation approach and strategy."""
    name: str
    description: str
    timeline_months: float
    resource_requirements: Dict[str, Any]
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"
    success_factors: List[str]
    phases: List[Dict[str, Any]]


class TransformationDomain(ABC):
    """Abstract base class that all transformation domains must implement."""
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Return the unique identifier for this domain."""
        pass
    
    @abstractmethod
    def get_domain_description(self) -> str:
        """Return human-readable description of this transformation type."""
        pass
    
    @abstractmethod
    def get_question_context(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide domain-specific context for AI question generation.
        
        Args:
            conversation_context: Current conversation state and context
            
        Returns:
            Dictionary containing domain-specific context for question generation
        """
        pass
    
    @abstractmethod
    async def assess_transformation_complexity(
        self, 
        discovered_facts: Dict[str, Any]
    ) -> ComplexityAssessment:
        """
        Assess the technical complexity and effort required for this transformation.
        
        Args:
            discovered_facts: Business facts discovered during conversation
            
        Returns:
            ComplexityAssessment with technical analysis
        """
        pass
    
    @abstractmethod
    async def calculate_transformation_benefits(
        self,
        current_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> BenefitModel:
        """
        Calculate the business benefits of this transformation.
        
        Args:
            current_state: Current system/process state
            target_state: Desired future state
            
        Returns:
            BenefitModel with quantified business value
        """
        pass
    
    @abstractmethod
    async def generate_implementation_strategies(
        self,
        assessment_context: Dict[str, Any]
    ) -> List[ImplementationStrategy]:
        """
        Generate possible implementation strategies for this transformation.
        
        Args:
            assessment_context: Technical assessment and business context
            
        Returns:
            List of possible implementation approaches
        """
        pass
    
    def get_common_pain_points(self) -> List[str]:
        """
        Return common pain points for this transformation domain.
        
        Default implementation returns empty list, domains should override.
        """
        return []
    
    def get_business_value_categories(self) -> List[str]:
        """
        Return the main categories of business value this transformation provides.
        
        Default implementation returns generic categories, domains should override.
        """
        return [
            "cost_reduction",
            "productivity_improvement", 
            "risk_mitigation",
            "strategic_advantage"
        ]
    
    def get_success_metrics(self) -> List[str]:
        """
        Return key metrics for measuring transformation success.
        
        Default implementation returns generic metrics, domains should override.
        """
        return [
            "roi_percentage",
            "payback_period_months",
            "user_satisfaction_score",
            "technical_debt_reduction"
        ]
    
    async def validate_transformation_feasibility(
        self,
        discovered_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate if the transformation is feasible based on discovered facts.
        
        Returns:
            Dictionary with feasibility assessment including blockers and recommendations
        """
        # Default implementation - domains can override for specific validation
        return {
            "is_feasible": True,
            "confidence": 0.7,
            "blockers": [],
            "recommendations": ["Conduct detailed technical assessment"],
            "alternative_approaches": []
        }
    
    def get_domain_keywords(self) -> List[str]:
        """
        Return keywords that help identify this domain from user input.
        
        Used by domain registry for auto-detection.
        """
        return []
    
    def calculate_effort_estimate(
        self,
        complexity_factors: Dict[str, float],
        team_context: Dict[str, Any]
    ) -> float:
        """
        Calculate effort estimate in person-weeks based on complexity and team.
        
        Default implementation provides basic calculation, domains should override.
        """
        base_complexity = sum(complexity_factors.values()) / len(complexity_factors)
        team_size = team_context.get("size", 3)
        team_experience = team_context.get("experience_level", 0.7)  # 0-1 scale
        
        # Basic calculation: complexity adjusted by team factors
        effort_weeks = (base_complexity * 8) / (team_size * team_experience)
        return max(2.0, effort_weeks)  # Minimum 2 weeks
    
    def estimate_business_impact(
        self,
        pain_points: List[str],
        team_size: int,
        current_velocity: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Estimate business impact based on pain points and team context.
        
        Default implementation provides basic estimates, domains should override.
        """
        # Basic impact estimation
        impact_multiplier = {
            "performance": 0.3,  # 30% improvement potential
            "productivity": 0.25,  # 25% productivity gain
            "maintenance": 0.4,  # 40% maintenance reduction
            "scalability": 0.5,  # 50% better scalability
        }
        
        total_impact = 0.0
        for pain_point in pain_points:
            for category, multiplier in impact_multiplier.items():
                if category in pain_point.lower():
                    total_impact += multiplier
        
        # Scale by team size (larger teams = larger absolute impact)
        team_scaling = min(2.0, team_size / 5)  # Scale up to 2x for teams of 10+
        
        return {
            "productivity_improvement": total_impact * team_scaling * 0.3,
            "cost_reduction": total_impact * team_scaling * 0.2,
            "quality_improvement": total_impact * team_scaling * 0.25,
            "risk_reduction": total_impact * team_scaling * 0.15
        }