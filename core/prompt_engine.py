"""
Prompt Engine - Template-based prompt management for AI interactions.

Provides Jinja2 templating with transformation-specific filters,
dynamic prompt composition, and version control for prompt templates.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import jinja2
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger


class PromptEngine:
    """Template-based prompt management system."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize prompt engine with template directory."""
        if template_dir is None:
            # Default to prompts directory relative to project root
            current_dir = Path(__file__).parent.parent
            template_dir = current_dir / "prompts"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup Jinja2 environment with custom filters
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,  # We're generating prompts, not HTML
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters for transformation-specific formatting
        self._add_custom_filters()
        
        logger.info(f"PromptEngine initialized with template directory: {self.template_dir}")
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)
            
            logger.debug(f"Rendered template '{template_name}' with context keys: {list(context.keys())}")
            return rendered.strip()
            
        except jinja2.TemplateNotFound:
            logger.error(f"Template '{template_name}' not found in {self.template_dir}")
            raise
        except jinja2.TemplateError as e:
            logger.error(f"Template rendering error in '{template_name}': {e}")
            raise
    
    def render_string(self, template_string: str, **context) -> str:
        """Render a template string directly."""
        try:
            template = self.env.from_string(template_string)
            rendered = template.render(**context)
            return rendered.strip()
        except jinja2.TemplateError as e:
            logger.error(f"String template rendering error: {e}")
            raise
    
    def list_templates(self, pattern: str = "*.jinja2") -> List[str]:
        """List available templates matching pattern."""
        templates = []
        for template_file in self.template_dir.rglob(pattern):
            relative_path = template_file.relative_to(self.template_dir)
            templates.append(str(relative_path))
        return sorted(templates)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        template_path = self.template_dir / template_name
        return template_path.exists()
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters for business and technical formatting."""
        
        def business_format(value, unit=''):
            """Format numbers for business context (K, M, B)."""
            if not isinstance(value, (int, float)):
                return str(value)
            
            if value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.1f}B{unit}"
            elif value >= 1_000_000:
                return f"{value / 1_000_000:.1f}M{unit}"
            elif value >= 1_000:
                return f"{value / 1_000:.1f}K{unit}"
            else:
                return f"{value:,.0f}{unit}"
        
        def percentage(value, precision=1):
            """Format as percentage."""
            if not isinstance(value, (int, float)):
                return str(value)
            return f"{value * 100:.{precision}f}%"
        
        def currency(value, symbol='$'):
            """Format as currency."""
            if not isinstance(value, (int, float)):
                return str(value)
            
            if value >= 1_000_000:
                return f"{symbol}{value / 1_000_000:.1f}M"
            elif value >= 1_000:
                return f"{symbol}{value / 1_000:.1f}K"
            else:
                return f"{symbol}{value:,.0f}"
        
        def confidence_level(value):
            """Convert confidence score to descriptive text."""
            if not isinstance(value, (int, float)):
                return str(value)
            
            if value >= 0.9:
                return "Very High"
            elif value >= 0.7:
                return "High"
            elif value >= 0.5:
                return "Moderate"
            elif value >= 0.3:
                return "Low"
            else:
                return "Very Low"
        
        def domain_friendly(value):
            """Convert domain type to user-friendly description."""
            domain_names = {
                'framework_migration': 'framework migration',
                'language_conversion': 'language conversion', 
                'modernization': 'system modernization',
                'performance_optimization': 'performance optimization',
                'architecture_redesign': 'architecture redesign',
                'dependency_upgrade': 'dependency upgrade'
            }
            return domain_names.get(str(value).lower(), str(value).replace('_', ' '))
        
        # Add filters to environment
        self.env.filters['business_format'] = business_format
        self.env.filters['percentage'] = percentage
        self.env.filters['currency'] = currency
        self.env.filters['confidence_level'] = confidence_level
        self.env.filters['domain_friendly'] = domain_friendly
    
    def create_template_from_string(self, template_name: str, template_content: str):
        """Create a new template file from string content."""
        template_path = self.template_dir / template_name
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        logger.info(f"Created template '{template_name}' at {template_path}")
    
    def get_template_content(self, template_name: str) -> str:
        """Get the raw content of a template."""
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()


# Default prompt templates as constants for bootstrapping
DEFAULT_TEMPLATES = {
    "business_discovery.jinja2": """You are a business analyst helping evaluate a {{ domain_context.domain_type | domain_friendly }} transformation.

CONTEXT:
- User request: "{{ user_request }}"
- Domain: {{ domain_context.domain_type | domain_friendly }}
- Current phase: Discovery

YOUR ROLE:
- Focus on business impact and ROI potential
- Ask questions that uncover quantifiable business value
- Maintain a friendly, consultative tone
- Avoid technical jargon, speak in business terms

GENERATE 3-5 BUSINESS-FOCUSED QUESTIONS:
The questions should help understand:
1. Current business pain points and costs
2. Impact on team productivity and velocity  
3. Customer/user experience implications
4. Competitive or strategic drivers
5. Success criteria and measurable outcomes

Make questions conversational and specific to {{ domain_context.domain_type | domain_friendly }}.

Example question format:
"How much time does your team currently spend dealing with [specific pain point]?"
"What business opportunities are you missing due to [current limitation]?"
"If we could improve [relevant metric] by 50%, what would that enable for your business?"

Generate the questions as a numbered list:""",

    "roi_calculation.jinja2": """Calculate the ROI for this {{ domain_type | domain_friendly }} transformation:

CURRENT STATE:
{% for key, value in current_state.items() %}
- {{ key | capitalize_words }}: {{ value }}
{% endfor %}

TARGET STATE:
{% for key, value in target_state.items() %}
- {{ key | capitalize_words }}: {{ value }}
{% endfor %}

TEAM INFORMATION:
- Team size: {{ team_info.size }} developers
- Average hourly rate: {{ team_info.hourly_rate | business_format }}
- Current productivity: {{ team_info.current_velocity }} features/month

CALCULATE:
1. Implementation costs (development time, infrastructure, training)
2. Annual operational savings (efficiency gains, cost reductions)
3. Revenue impact (performance improvements, faster delivery)
4. Risk mitigation value (security, compliance, technical debt)

Present results in business-friendly format with:
- Total investment required
- Annual benefits breakdown  
- ROI percentage and payback period
- Confidence level and key assumptions
- Go/No-go recommendation with reasoning""",

    "executive_summary.jinja2": """# {{ transformation_type | domain_friendly }} Business Case

## Executive Summary

**Transformation**: {{ current_state.description }} → {{ target_state.description }}

**Investment**: {{ business_case.total_investment | business_format }} over {{ business_case.timeline_months }} months

**Returns**: {{ business_case.annual_benefits | business_format }}/year in quantified benefits

**ROI**: {{ business_case.roi | percentage }} with {{ business_case.payback_period_months }} month payback

**Recommendation**: {{ business_case.recommendation }}

## Business Drivers

{% for driver in business_drivers %}
- **{{ driver.category }}**: {{ driver.description }}
  - Current impact: {{ driver.current_cost | business_format }}/year
  - Improvement potential: {{ driver.improvement_potential | percentage }}
{% endfor %}

## Investment Breakdown

| Category | Cost | Timeline |
|----------|------|----------|
{% for cost in business_case.cost_breakdown %}
| {{ cost.category }} | {{ cost.amount | business_format }} | {{ cost.duration | time_format }} |
{% endfor %}

## Expected Benefits

| Benefit Category | Annual Value | Confidence |
|------------------|--------------|------------|
{% for benefit in business_case.benefits %}
| {{ benefit.category }} | {{ benefit.annual_value | business_format }} | {{ benefit.confidence | percentage }} |
{% endfor %}

## Risk Assessment

{% for risk in business_case.risks %}
- **{{ risk.category }}**: {{ risk.description }}
  - Probability: {{ risk.probability | percentage }}
  - Impact: {{ risk.impact | business_format }}
  - Mitigation: {{ risk.mitigation_strategy }}
{% endfor %}

## Next Steps

1. **Approval**: Stakeholder review and decision
2. **Planning**: Detailed implementation roadmap  
3. **Execution**: {{ business_case.recommended_approach }}
4. **Monitoring**: Success metrics and progress tracking

**Decision Required By**: {{ decision_deadline }}
**Recommended Start Date**: {{ recommended_start_date }}"""
}


def bootstrap_default_templates(prompt_engine: PromptEngine):
    """Create default templates if they don't exist."""
    for template_name, content in DEFAULT_TEMPLATES.items():
        if not prompt_engine.template_exists(template_name):
            prompt_engine.create_template_from_string(template_name, content)
    
    logger.info(f"Bootstrapped {len(DEFAULT_TEMPLATES)} default templates")