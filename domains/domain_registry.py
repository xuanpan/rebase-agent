"""
Domain Registry - Central registry and auto-detection for transformation domains.

Manages registration, discovery, and intelligent routing of transformation
requests to appropriate domain implementations.
"""

import importlib
import pkgutil
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import re
from loguru import logger

from .base_domain import TransformationDomain


class DomainRegistry:
    """Central registry for all transformation domains with auto-detection."""
    
    def __init__(self):
        self._domains: Dict[str, TransformationDomain] = {}
        self._domain_keywords: Dict[str, List[str]] = {}
        self._auto_discovery_enabled = True
        
        # Auto-discover domains on initialization
        if self._auto_discovery_enabled:
            self._auto_discover_domains()
        
        logger.info(f"DomainRegistry initialized with {len(self._domains)} domains")
    
    def register_domain(self, domain: TransformationDomain):
        """Register a transformation domain."""
        domain_name = domain.get_domain_name()
        
        if domain_name in self._domains:
            logger.warning(f"Overriding existing domain: {domain_name}")
        
        self._domains[domain_name] = domain
        self._domain_keywords[domain_name] = domain.get_domain_keywords()
        
        logger.info(f"Registered domain: {domain_name}")
    
    def get_domain(self, domain_name: str) -> Optional[TransformationDomain]:
        """Get a domain by name."""
        return self._domains.get(domain_name)
    
    def list_domains(self) -> List[str]:
        """List all registered domain names."""
        return list(self._domains.keys())
    
    def get_domain_info(self, domain_name: str) -> Optional[Dict[str, any]]:
        """Get information about a domain."""
        domain = self._domains.get(domain_name)
        if not domain:
            return None
        
        return {
            "name": domain.get_domain_name(),
            "description": domain.get_domain_description(),
            "keywords": domain.get_domain_keywords(),
            "pain_points": domain.get_common_pain_points(),
            "value_categories": domain.get_business_value_categories(),
            "success_metrics": domain.get_success_metrics()
        }
    
    async def auto_detect_domain(self, user_request: str) -> TransformationDomain:
        """
        Auto-detect the most appropriate domain based on user request.
        
        Uses keyword matching and pattern analysis to determine the best domain.
        """
        user_request_lower = user_request.lower()
        domain_scores = {}
        
        # Score domains based on keyword matches
        for domain_name, keywords in self._domain_keywords.items():
            score = 0.0
            
            # Direct keyword matching
            for keyword in keywords:
                if keyword.lower() in user_request_lower:
                    score += 1.0
            
            # Pattern-based scoring
            score += self._calculate_pattern_score(user_request_lower, domain_name)
            
            if score > 0:
                domain_scores[domain_name] = score
        
        if not domain_scores:
            # No matches found, return default (modernization)
            logger.warning(f"No domain matches found for: {user_request}")
            return self._get_default_domain()
        
        # Return highest scoring domain
        best_match = max(domain_scores.items(), key=lambda x: x[1])
        best_domain_name = best_match[0]
        confidence = best_match[1]
        
        logger.info(f"Auto-detected domain: {best_domain_name} (confidence: {confidence:.2f})")
        return self._domains[best_domain_name]
    
    def suggest_domains(self, user_request: str, limit: int = 3) -> List[Tuple[str, float]]:
        """
        Suggest possible domains for a user request with confidence scores.
        
        Returns list of (domain_name, confidence_score) tuples.
        """
        user_request_lower = user_request.lower()
        domain_scores = {}
        
        for domain_name, keywords in self._domain_keywords.items():
            score = 0.0
            
            # Keyword matching
            for keyword in keywords:
                if keyword.lower() in user_request_lower:
                    score += 1.0
            
            # Pattern scoring
            score += self._calculate_pattern_score(user_request_lower, domain_name)
            
            domain_scores[domain_name] = score
        
        # Sort by score and return top matches
        sorted_scores = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:limit]
    
    def _auto_discover_domains(self):
        """Automatically discover and register domains from domains/ folder."""
        try:
            domains_path = Path(__file__).parent
            
            for item in domains_path.iterdir():
                if item.is_dir() and not item.name.startswith('__'):
                    self._try_load_domain_module(item.name)
                    
        except Exception as e:
            logger.error(f"Error during domain auto-discovery: {e}")
    
    def _try_load_domain_module(self, module_name: str):
        """Try to load a domain module and register it."""
        try:
            module_path = f"domains.{module_name}"
            module = importlib.import_module(module_path)
            
            # Look for get_domain_instance function
            if hasattr(module, 'get_domain_instance'):
                domain_instance = module.get_domain_instance()
                if isinstance(domain_instance, TransformationDomain):
                    self.register_domain(domain_instance)
                else:
                    logger.warning(f"get_domain_instance in {module_name} did not return TransformationDomain")
            else:
                logger.debug(f"Domain module {module_name} has no get_domain_instance function")
                
        except Exception as e:
            logger.warning(f"Could not load domain module {module_name}: {e}")
    
    def _calculate_pattern_score(self, user_request: str, domain_name: str) -> float:
        """Calculate pattern-based scoring for domain matching."""
        score = 0.0
        
        # Framework migration patterns
        if domain_name == "framework_migration":
            framework_patterns = [
                r'migrate.*from.*to',
                r'switch.*from.*to', 
                r'convert.*to',
                r'react.*vue|vue.*react',
                r'angular.*react|react.*angular',
                r'django.*fastapi|fastapi.*django'
            ]
            for pattern in framework_patterns:
                if re.search(pattern, user_request):
                    score += 0.8
        
        # Language conversion patterns  
        elif domain_name == "language_conversion":
            language_patterns = [
                r'python.*go|go.*python',
                r'javascript.*typescript|typescript.*javascript',
                r'java.*kotlin|kotlin.*java',
                r'rewrite.*in',
                r'convert.*language'
            ]
            for pattern in language_patterns:
                if re.search(pattern, user_request):
                    score += 0.8
        
        # Performance optimization patterns
        elif domain_name == "performance_optimization":
            performance_patterns = [
                r'slow|performance|speed|optimize',
                r'improve.*performance',
                r'faster|slower',
                r'bottleneck|latency'
            ]
            for pattern in performance_patterns:
                if re.search(pattern, user_request):
                    score += 0.6
        
        # Architecture redesign patterns
        elif domain_name == "architecture_redesign":
            architecture_patterns = [
                r'monolith.*microservices|microservices.*monolith',
                r'architecture|redesign|restructure',
                r'scalability|scale',
                r'distributed|decoupled'
            ]
            for pattern in architecture_patterns:
                if re.search(pattern, user_request):
                    score += 0.7
        
        # Dependency upgrade patterns
        elif domain_name == "dependency_upgrade":
            dependency_patterns = [
                r'upgrade|update|patch',
                r'security.*fix|vulnerability',
                r'deprecated|legacy.*library',
                r'end.*of.*life|eol'
            ]
            for pattern in dependency_patterns:
                if re.search(pattern, user_request):
                    score += 0.6
        
        # Modernization patterns (catch-all)
        elif domain_name == "modernization":
            modernization_patterns = [
                r'modernize|legacy|old.*system',
                r'outdated|obsolete',
                r'transformation|overhaul'
            ]
            for pattern in modernization_patterns:
                if re.search(pattern, user_request):
                    score += 0.5
        
        return score
    
    def _get_default_domain(self) -> TransformationDomain:
        """Get the default domain when no matches are found."""
        # Try to return modernization as default
        if "modernization" in self._domains:
            return self._domains["modernization"]
        
        # Otherwise return the first available domain
        if self._domains:
            return next(iter(self._domains.values()))
        
        # If no domains are registered, this is a configuration error
        raise RuntimeError("No transformation domains are registered")
    
    def validate_all_domains(self) -> Dict[str, bool]:
        """Validate all registered domains implement required methods."""
        validation_results = {}
        
        for domain_name, domain in self._domains.items():
            try:
                # Test required methods exist and are callable
                required_methods = [
                    'get_domain_name',
                    'get_domain_description', 
                    'get_question_context',
                    'assess_transformation_complexity',
                    'calculate_transformation_benefits',
                    'generate_implementation_strategies'
                ]
                
                all_methods_valid = True
                for method_name in required_methods:
                    if not hasattr(domain, method_name):
                        logger.error(f"Domain {domain_name} missing method: {method_name}")
                        all_methods_valid = False
                    elif not callable(getattr(domain, method_name)):
                        logger.error(f"Domain {domain_name} method not callable: {method_name}")
                        all_methods_valid = False
                
                validation_results[domain_name] = all_methods_valid
                
            except Exception as e:
                logger.error(f"Error validating domain {domain_name}: {e}")
                validation_results[domain_name] = False
        
        return validation_results
    
    def reload_domains(self):
        """Reload all domains (useful for development)."""
        logger.info("Reloading all domains...")
        self._domains.clear()
        self._domain_keywords.clear()
        self._auto_discover_domains()
        logger.info(f"Reloaded {len(self._domains)} domains")