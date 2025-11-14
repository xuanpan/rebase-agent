"""Discovery models for business data collection."""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class DiscoveryCategory:
    """Represents a discovery category with progress tracking and current vs future state fields."""
    name: str
    progress: float = 0.0  # 0.0 to 1.0
    completion_status: str = "not_started"  # "not_started" | "in_progress" | "complete"
    summary: str = ""
    current_state: Dict[str, Any] = None  # Current/existing state data
    future_state: Dict[str, Any] = None   # Desired future state data
    
    def __post_init__(self):
        if self.current_state is None:
            self.current_state = {}
        if self.future_state is None:
            self.future_state = {}


@dataclass
class CollectedBusinessData:
    """Hierarchical business data collection with parent categories and child fields."""
    
    # Parent Categories (5 core discovery areas for ROI-focused analysis)
    business_goals: DiscoveryCategory = None
    stakeholders: DiscoveryCategory = None  
    current_problems: DiscoveryCategory = None
    key_metrics: DiscoveryCategory = None
    implementation_context: DiscoveryCategory = None
    
    def __post_init__(self):
        """Initialize discovery categories with their child fields."""
        
        # Initialize Business Goals category
        if self.business_goals is None:
            self.business_goals = DiscoveryCategory(
                name="Business Goals",
                current_state={},
                future_state={
                    "primary_objectives": [],     # Main business goals
                    "success_criteria": [],       # How success is measured
                    "kpis": [],                   # Key performance indicators
                    "strategic_alignment": "",    # How this fits company strategy
                    "timeline_goals": {}          # {"short_term": [], "long_term": []}
                }
            )
        
        # Initialize Stakeholders category
        if self.stakeholders is None:
            self.stakeholders = DiscoveryCategory(
                name="Stakeholders",
                current_state={
                    "decision_makers": [],        # [{"name": str, "role": str, "influence": str}]
                    "technical_team": [],         # Engineering stakeholders
                    "business_users": [],         # End users and business stakeholders
                    "external_stakeholders": [],  # Customers, partners, vendors
                    "project_sponsors": []        # Executive sponsors
                },
                future_state={
                    "communication_plan": {},     # How to keep stakeholders informed
                    "change_management": [],      # Training, adoption strategies
                    "resource_needs": {}          # Additional team members needed
                }
            )
        
        # Initialize Current Problems category  
        if self.current_problems is None:
            self.current_problems = DiscoveryCategory(
                name="Current Problems",
                current_state={
                    "technical_issues": [],       # Technical debt, legacy problems
                    "process_inefficiencies": [], # Workflow problems
                    "user_complaints": [],        # User-reported issues
                    "security_risks": [],         # Current security vulnerabilities
                    "compliance_risks": [],       # Regulatory compliance gaps
                    "reliability_issues": [],     # System downtime, failures
                    "operational_risks": [],      # Maintenance, support issues
                    "cost_drains": []             # Areas causing financial loss
                },
                future_state={}  # Problems should be resolved, so future state is empty
            )
        
        # Initialize Key Metrics category
        if self.key_metrics is None:
            self.key_metrics = DiscoveryCategory(
                name="Key Metrics",
                current_state={
                    "performance_metrics": {},    # {"response_time": "2s", "throughput": "100/min"}
                    "business_metrics": {},       # {"revenue": "$1M", "conversion_rate": "2%"}
                    "operational_metrics": {},    # {"uptime": "99%", "error_rate": "5%"}
                    "operational_costs": {},      # {"infrastructure": "$5k/month", "maintenance": "$2k/month", "licenses": "$1k/month"}
                    "user_metrics": {},           # {"satisfaction": "6/10", "adoption": "60%"}
                    "security_metrics": {}        # {"incidents": "5/month", "vulnerabilities": "20"}
                },
                future_state={
                    "performance_targets": {},    # Target performance metrics
                    "business_targets": {},       # Target business metrics  
                    "operational_targets": {},    # Target operational metrics
                    "cost_savings_targets": {},   # Target operational cost reductions
                    "user_targets": {},           # Target user experience
                    "security_targets": {}        # Target security improvements
                }
            )
        
        # Initialize Implementation Context category
        if self.implementation_context is None:
            self.implementation_context = DiscoveryCategory(
                name="Implementation Context",
                current_state={
                    "team_capacity": {},          # Current team size, skills, availability
                    "technical_constraints": [], # Current system limitations
                    "organizational_readiness": {} # Change management readiness
                },
                future_state={
                    "project_budget": {},         # {"max_investment": float, "budget_flexibility": str, "funding_source": str}
                    "resource_plan": {},          # {"team_size_needed": int, "expertise_required": [], "external_help": bool}
                    "timeline_requirements": {},  # {"hard_deadline": str, "preferred_timeline": str}
                    "regulatory_compliance": [],  # Compliance requirements to meet
                    "business_constraints": [],   # Organizational limitations
                    "implementation_risks": []    # Project execution risks
                }
            )
    
    def get_category_progress(self, category_name: str) -> float:
        """Calculate progress for a specific discovery category."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return 0.0
        
        # Count non-empty fields in both current_state and future_state
        total_fields = len(category.current_state) + len(category.future_state)
        completed_fields = 0
        
        # Check current_state fields
        for field_name, field_value in category.current_state.items():
            if field_value:  # Not None and not empty
                if isinstance(field_value, list) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, dict) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, str) and field_value.strip():
                    completed_fields += 1
        
        # Check future_state fields  
        for field_name, field_value in category.future_state.items():
            if field_value:  # Not None and not empty
                if isinstance(field_value, list) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, dict) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, str) and field_value.strip():
                    completed_fields += 1
        
        progress = completed_fields / total_fields if total_fields > 0 else 0.0
        category.progress = progress
        
        # Update completion status
        if progress == 0.0:
            category.completion_status = "not_started"
        elif progress < 1.0:
            category.completion_status = "in_progress"
        else:
            category.completion_status = "complete"
        
        return progress
    
    def get_overall_completeness_score(self) -> float:
        """Calculate overall discovery completeness across all categories."""
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        total_progress = sum(self.get_category_progress(cat) for cat in categories)
        return total_progress / len(categories)
    
    def get_missing_categories(self) -> List[str]:
        """Get categories that need more information."""
        missing = []
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        
        for cat_name in categories:
            progress = self.get_category_progress(cat_name)
            if progress < 0.5:  # Less than 50% complete
                missing.append(cat_name)
        
        return missing
    
    def update_category_field(self, category_name: str, field_name: str, value: Any, state_type: str = "current_state"):
        """Update a specific field within a category's current or future state."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return
        
        # Get the appropriate state dict
        state_dict = category.current_state if state_type == "current_state" else category.future_state
        
        if field_name in state_dict:
            if isinstance(value, list) and isinstance(state_dict[field_name], list):
                state_dict[field_name].extend(value)
            else:
                state_dict[field_name] = value
        
        # Update progress after modification
        self.get_category_progress(category_name)
        
        # Generate category summary
        self._update_category_summary(category_name)
    
    def _update_category_summary(self, category_name: str):
        """Generate a human-readable summary for a category based on its current and future state fields."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return
        
        if category_name == "business_goals":
            objectives = category.future_state.get("primary_objectives", [])
            kpis = category.future_state.get("kpis", [])
            summary_parts = []
            if objectives:
                summary_parts.append(f"{len(objectives)} primary objectives")
            if kpis:
                summary_parts.append(f"{len(kpis)} KPIs defined")
            category.summary = ", ".join(summary_parts) if summary_parts else "No goals defined yet"
            
        elif category_name == "current_problems":
            tech_issues = category.current_state.get("technical_issues", [])
            security_risks = category.current_state.get("security_risks", [])
            summary_parts = []
            if tech_issues:
                summary_parts.append(f"{len(tech_issues)} technical issues")
            if security_risks:
                summary_parts.append(f"{len(security_risks)} security risks")
            category.summary = ", ".join(summary_parts) if summary_parts else "No problems identified"
            
        elif category_name == "stakeholders":
            decision_makers = category.current_state.get("decision_makers", [])
            team = category.current_state.get("technical_team", [])
            users = category.current_state.get("business_users", [])
            total_stakeholders = len(decision_makers) + len(team) + len(users)
            category.summary = f"{total_stakeholders} stakeholders identified" if total_stakeholders > 0 else "No stakeholders identified"
            
        elif category_name == "key_metrics":
            current_metrics = len([v for v in category.current_state.values() if v])
            target_metrics = len([v for v in category.future_state.values() if v])
            
            # Check for operational costs specifically
            operational_costs = category.current_state.get("operational_costs", {})
            cost_savings = category.future_state.get("cost_savings_targets", {})
            
            summary_parts = []
            if current_metrics > 0:
                summary_parts.append(f"{current_metrics} current metrics")
            if target_metrics > 0:
                summary_parts.append(f"{target_metrics} targets")
            if operational_costs:
                summary_parts.append(f"operational costs tracked")
            if cost_savings:
                summary_parts.append(f"savings targets set")
                
            category.summary = ", ".join(summary_parts) if summary_parts else "No metrics defined"
        
        elif category_name == "implementation_context":
            current_context = len([v for v in category.current_state.values() if v and (isinstance(v, list) and len(v) > 0 or isinstance(v, dict) and len(v) > 0 or isinstance(v, str) and v.strip())])
            future_context = len([v for v in category.future_state.values() if v and (isinstance(v, list) and len(v) > 0 or isinstance(v, dict) and len(v) > 0 or isinstance(v, str) and v.strip())])
            
            # Check for project budget specifically
            project_budget = category.future_state.get("project_budget", {})
            resource_plan = category.future_state.get("resource_plan", {})
            
            summary_parts = []
            if current_context > 0:
                summary_parts.append(f"{current_context} current constraints")
            if project_budget:
                summary_parts.append("project budget defined")
            if resource_plan:
                summary_parts.append("resource plan set")
                
            category.summary = ", ".join(summary_parts) if summary_parts else "Implementation context not defined"
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        """Get a complete discovery summary for display."""
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        summary = {
            "overall_progress": self.get_overall_completeness_score(),
            "categories": {}
        }
        
        for cat_name in categories:
            category = getattr(self, cat_name.lower().replace(" ", "_"))
            if category:
                summary["categories"][cat_name] = {
                    "name": category.name,
                    "progress": category.progress,
                    "status": category.completion_status,
                    "summary": category.summary,
                    "current_state": category.current_state,
                    "future_state": category.future_state
                }
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectedBusinessData':
        """Create instance from dictionary."""
        # Convert nested dictionaries to dataclass instances
        def convert_category(cat_dict, name):
            if isinstance(cat_dict, dict):
                return DiscoveryCategory(
                    name=name,
                    progress=cat_dict.get('progress', 0.0),
                    completion_status=cat_dict.get('completion_status', 'not_started'),
                    summary=cat_dict.get('summary', ''),
                    current_state=cat_dict.get('current_state', {}),
                    future_state=cat_dict.get('future_state', {})
                )
            return cat_dict
        
        return cls(
            business_goals=convert_category(data.get('business_goals'), 'Business Goals'),
            stakeholders=convert_category(data.get('stakeholders'), 'Stakeholders'),  
            current_problems=convert_category(data.get('current_problems'), 'Current Problems'),
            key_metrics=convert_category(data.get('key_metrics'), 'Key Metrics'),
            implementation_context=convert_category(data.get('implementation_context'), 'Implementation Context')
        )