"""
Tests de Sécurité - Suite de tests pour la sécurité du système FinAgent

Cette suite valide la sécurité du système concernant:
- Protection des clés API et credentials
- Validation et sanitization des inputs
- Prévention des injections et attaques
- Gestion sécurisée des données sensibles
- Authentification et autorisation
- Conformité aux standards de sécurité
"""

# Markers pour tests de sécurité
SECURITY_MARKERS = {
    "api_security": "Tests de sécurité API",
    "input_validation": "Tests de validation d'entrées",
    "credential_protection": "Tests de protection des credentials",
    "injection_prevention": "Tests de prévention d'injections",
    "data_protection": "Tests de protection des données",
    "authentication": "Tests d'authentification",
    "authorization": "Tests d'autorisation",
    "crypto": "Tests cryptographiques"
}

# Configuration des tests de sécurité
SECURITY_CONFIG = {
    "max_password_attempts": 3,
    "session_timeout_minutes": 30,
    "min_password_length": 8,
    "require_password_complexity": True,
    "api_rate_limit_per_minute": 60,
    "sensitive_data_patterns": [
        r"sk-[a-zA-Z0-9]{32,}",  # OpenAI API keys
        r"[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}",  # Credit card format
        r"[a-zA-Z0-9]{24,}",  # Generic API tokens
    ],
    "blocked_patterns": [
        r"<script.*?>.*?</script>",  # XSS
        r"union\s+select",  # SQL injection
        r"\bexec\s*\(",  # Code execution
        r"javascript:",  # JavaScript execution
    ]
}

__all__ = [
    "SECURITY_MARKERS",
    "SECURITY_CONFIG"
]