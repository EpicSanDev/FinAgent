"""
Tests de Robustesse - Suite de tests pour la robustesse du système FinAgent

Cette suite valide la capacité du système à:
- Gérer les erreurs de manière gracieuse
- Se récupérer des pannes et exceptions
- Maintenir la cohérence des données
- Gérer les cas limites et edge cases
- Assurer la fault tolerance
"""

# Markers pour tests de robustesse
ROBUSTNESS_MARKERS = {
    "error_handling": "Tests de gestion d'erreurs",
    "fault_tolerance": "Tests de tolérance aux pannes", 
    "recovery": "Tests de récupération",
    "edge_cases": "Tests de cas limites",
    "data_integrity": "Tests d'intégrité des données",
    "resilience": "Tests de résilience",
    "graceful_degradation": "Tests de dégradation gracieuse"
}

# Configuration des tests de robustesse
ROBUSTNESS_CONFIG = {
    "max_error_rate": 0.05,  # 5% max d'erreurs acceptées
    "recovery_timeout": 30.0,  # 30 secondes max pour récupération
    "data_corruption_tolerance": 0.001,  # 0.1% max corruption tolérée
    "retry_attempts": 3,  # Nombre tentatives de retry
    "circuit_breaker_threshold": 5  # Seuil déclenchement circuit breaker
}

__all__ = [
    "ROBUSTNESS_MARKERS",
    "ROBUSTNESS_CONFIG"
]