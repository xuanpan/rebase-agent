"""
Framework Migration Domain

Handles business-focused analysis and planning for framework-to-framework
transformations like React→Vue, Django→FastAPI, Angular→Svelte, etc.
"""

from typing import Dict, Any, List
from ..base_domain import (
    TransformationDomain, 
    ComplexityAssessment, 
    BenefitModel, 
    ImplementationStrategy
)


class FrameworkMigrationDomain(TransformationDomain):
    """Domain for framework-to-framework migration analysis."""
    
    def get_domain_name(self) -> str:
        return "framework_migration"
    
    def get_domain_description(self) -> str:
        return "Framework-to-framework transformations (React→Vue, Django→FastAPI, etc.)"
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "migrate", "migration", "framework", "react", "vue", "angular", 
            "svelte", "django", "fastapi", "express", "nestjs", "spring",
            "switch", "convert", "from", "to"
        ]
    
    def get_common_pain_points(self) -> List[str]:
        return [
            "complex_state_management",
            "steep_learning_curve", 
            "poor_developer_experience",
            "slow_development_velocity",
            "maintenance_overhead",
            "outdated_ecosystem",
            "performance_issues",
            "limited_community_support"
        ]
    
    def get_business_value_categories(self) -> List[str]:
        return [
            "developer_productivity",
            "maintenance_cost_reduction",
            "performance_improvements", 
            "talent_acquisition_advantage",
            "ecosystem_benefits",
            "future_proofing"
        ]
    
    def get_question_context(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build framework-specific context for question generation."""
        
        session_context = conversation_context.get("session_context", {})
        discovered_facts = getattr(session_context, 'discovered_facts', {})
        
        return {
            "domain_type": "framework_migration",
            "transformation_focus": "developer_productivity_and_maintainability",
            "business_impact_areas": [
                "development_velocity",
                "code_maintainability", 
                "team_satisfaction",
                "recruitment_and_retention",
                "technical_debt_reduction"
            ],
            "quantification_opportunities": [
                "hours_saved_per_developer_per_week",
                "bug_reduction_percentage", 
                "feature_delivery_speed_improvement",
                "onboarding_time_reduction",
                "maintenance_cost_savings"
            ],
            "common_migration_drivers": [
                "performance_bottlenecks",
                "developer_experience_issues",
                "ecosystem_limitations", 
                "maintenance_burden",
                "talent_market_alignment"
            ],
            "success_measurement_areas": [
                "developer_satisfaction_scores",
                "deployment_frequency",
                "bug_report_volume",
                "new_hire_productivity_timeline"
            ]
        }
    
    async def assess_transformation_complexity(
        self, 
        discovered_facts: Dict[str, Any]
    ) -> ComplexityAssessment:
        """Assess framework migration complexity."""
        
        # Extract key factors affecting complexity
        component_count = discovered_facts.get("component_count", 50)
        team_size = discovered_facts.get("team_size", 3)
        current_framework = discovered_facts.get("current_framework", "unknown")
        target_framework = discovered_facts.get("target_framework", "unknown")
        
        # Calculate complexity factors
        component_complexity = min(8.0, component_count / 25)  # Scale 1-8
        team_complexity = max(2.0, 6.0 - team_size * 0.5)  # Larger teams = lower complexity
        
        # Framework-specific complexity adjustments
        framework_complexity = self._assess_framework_migration_complexity(
            current_framework, target_framework
        )
        
        overall_score = (component_complexity + team_complexity + framework_complexity) / 3
        
        # Risk factors
        risk_factors = []
        if component_count > 100:
            risk_factors.append("Large codebase increases migration risk")
        if team_size < 2:
            risk_factors.append("Small team may struggle with migration workload") 
        if "legacy" in discovered_facts.get("current_state", "").lower():
            risk_factors.append("Legacy patterns may complicate migration")
        
        return ComplexityAssessment(
            overall_score=overall_score,
            technical_complexity=component_complexity,
            business_disruption=3.0,  # Framework migrations are moderately disruptive
            resource_requirements=team_complexity,
            timeline_estimate_weeks=max(4, component_count / 10),
            risk_factors=risk_factors,
            success_probability=max(0.6, 1.0 - (overall_score - 5.0) * 0.1)
        )
    
    async def calculate_transformation_benefits(
        self,
        current_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> BenefitModel:
        """Calculate framework migration business benefits."""
        
        team_size = current_state.get("team_size", 3)
        avg_salary = current_state.get("avg_developer_salary", 100000)
        current_velocity = current_state.get("features_per_month", 8)
        
        # Developer productivity improvements
        productivity_improvement = 0.25  # 25% productivity gain typical for good migrations
        annual_productivity_value = team_size * avg_salary * productivity_improvement
        
        # Maintenance cost reductions
        maintenance_reduction = 0.30  # 30% reduction in maintenance time
        annual_maintenance_savings = team_size * avg_salary * 0.2 * maintenance_reduction
        
        # Performance and user experience gains
        # Assume better framework leads to 10% better performance → 5% better conversion
        annual_revenue_impact = current_state.get("annual_revenue", 1000000) * 0.05
        
        # Risk mitigation (technical debt, security, vendor lock-in)
        risk_mitigation_value = 50000  # Estimated annual risk reduction value
        
        total_benefits = (
            annual_productivity_value + 
            annual_maintenance_savings + 
            annual_revenue_impact + 
            risk_mitigation_value
        )
        
        return BenefitModel(
            annual_cost_savings=annual_productivity_value + annual_maintenance_savings,
            annual_revenue_gains=annual_revenue_impact,
            productivity_improvements=annual_productivity_value,
            risk_mitigation_value=risk_mitigation_value,
            total_annual_benefits=total_benefits,
            confidence_level=0.75
        )
    
    async def generate_implementation_strategies(
        self,
        assessment_context: Dict[str, Any]
    ) -> List[ImplementationStrategy]:
        """Generate framework migration implementation strategies."""
        
        component_count = assessment_context.get("component_count", 50)
        team_size = assessment_context.get("team_size", 3)
        
        strategies = []
        
        # Strategy 1: Incremental Migration
        strategies.append(ImplementationStrategy(
            name="Incremental Component Migration",
            description="Migrate components one by one, maintaining parallel systems temporarily",
            timeline_months=max(3, component_count / 20),
            resource_requirements={
                "developers": team_size,
                "qa_engineers": 1,
                "devops_support": 0.5
            },
            risk_level="LOW",
            success_factors=[
                "Strong component architecture",
                "Good test coverage",
                "Team commitment to dual maintenance"
            ],
            phases=[
                {"phase": "Setup", "duration_weeks": 2, "description": "Setup build systems and tooling"},
                {"phase": "Core Components", "duration_weeks": 4, "description": "Migrate shared/core components"},
                {"phase": "Feature Components", "duration_weeks": 8, "description": "Migrate feature-specific components"},
                {"phase": "Integration", "duration_weeks": 2, "description": "Final integration and cleanup"}
            ]
        ))
        
        # Strategy 2: Big Bang Migration (for smaller codebases)
        if component_count <= 50:
            strategies.append(ImplementationStrategy(
                name="Complete Rewrite",
                description="Full migration in dedicated sprint cycles",
                timeline_months=2,
                resource_requirements={
                    "developers": team_size,
                    "qa_engineers": 1,
                    "project_manager": 0.5
                },
                risk_level="MEDIUM",
                success_factors=[
                    "Small, manageable codebase",
                    "Strong team expertise in target framework",
                    "Comprehensive test suite"
                ],
                phases=[
                    {"phase": "Planning", "duration_weeks": 1, "description": "Detailed migration planning"},
                    {"phase": "Core Migration", "duration_weeks": 4, "description": "Migrate all components"},
                    {"phase": "Testing & Polish", "duration_weeks": 2, "description": "Comprehensive testing"},
                    {"phase": "Deployment", "duration_weeks": 1, "description": "Production deployment"}
                ]
            ))
        
        # Strategy 3: Strangler Fig Pattern (for large applications)
        if component_count > 100:
            strategies.append(ImplementationStrategy(
                name="Strangler Fig Migration",
                description="Gradually replace old framework by building new features in target framework",
                timeline_months=max(6, component_count / 15),
                resource_requirements={
                    "developers": team_size + 1,
                    "architect": 0.5,
                    "qa_engineers": 1
                },
                risk_level="LOW",
                success_factors=[
                    "Clear feature boundaries",
                    "Good API design",
                    "Long-term organizational commitment"
                ],
                phases=[
                    {"phase": "Architecture Design", "duration_weeks": 3, "description": "Design integration architecture"},
                    {"phase": "New Features Only", "duration_weeks": 12, "description": "Build new features in target framework"},
                    {"phase": "Legacy Migration", "duration_weeks": 20, "description": "Gradually migrate existing features"},
                    {"phase": "Cleanup", "duration_weeks": 4, "description": "Remove old framework dependencies"}
                ]
            ))
        
        return strategies
    
    def _assess_framework_migration_complexity(
        self, 
        current_framework: str, 
        target_framework: str
    ) -> float:
        """Assess complexity based on specific framework migration path."""
        
        # Complexity matrix based on framework similarity and ecosystem maturity
        complexity_matrix = {
            # React migrations
            ("react", "vue"): 4.0,      # Moderate complexity
            ("react", "svelte"): 5.0,   # Higher complexity (different paradigms)
            ("react", "angular"): 6.0,  # High complexity (very different)
            
            # Vue migrations  
            ("vue", "react"): 4.5,      # Moderate complexity
            ("vue", "svelte"): 4.0,     # Similar reactive paradigms
            
            # Backend framework migrations
            ("django", "fastapi"): 5.5, # Significant paradigm shift
            ("express", "nestjs"): 4.0, # Similar Node.js ecosystem
            ("spring", "django"): 7.0,  # Language + framework change
        }
        
        key = (current_framework.lower(), target_framework.lower())
        return complexity_matrix.get(key, 5.0)  # Default moderate complexity


def get_domain_instance() -> TransformationDomain:
    """Entry point for domain auto-discovery."""
    return FrameworkMigrationDomain()