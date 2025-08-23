"""
Tests de Sécurité - Sécurité des APIs et Credentials

Ces tests valident la sécurité des APIs, la protection des clés
d'accès, la gestion sécurisée des credentials et la prévention
des fuites de données sensibles.
"""

import pytest
import os
import re
import json
import tempfile
import base64
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from unittest.mock import Mock, patch, MagicMock
import logging
from datetime import datetime, timedelta

from finagent.business.providers.openbb_provider import OpenBBProvider
from finagent.business.providers.claude_provider import ClaudeProvider
from finagent.business.exceptions import APIError, ConfigurationError

# Import des utilitaires de test
from tests.utils import MockOpenBBProvider, MockClaudeProvider
from tests.security import SECURITY_CONFIG


@dataclass
class SecurityTestResult:
    """Résultat de test de sécurité"""
    test_name: str
    security_check_type: str
    vulnerability_detected: bool
    security_level: str  # "high", "medium", "low"
    remediation_required: bool
    compliance_score: float


class CredentialProtectionTester:
    """Testeur de protection des credentials"""
    
    def __init__(self):
        self.sensitive_patterns = SECURITY_CONFIG["sensitive_data_patterns"]
        self.detection_log = []
    
    def scan_for_exposed_credentials(self, data: Any, context: str = "") -> List[Dict[str, Any]]:
        """Scanne pour des credentials exposés"""
        exposed_credentials = []
        
        # Convertir en string pour analyse
        if isinstance(data, dict):
            content = json.dumps(data, indent=2)
        elif isinstance(data, list):
            content = str(data)
        else:
            content = str(data)
        
        # Chercher patterns sensibles
        for pattern in self.sensitive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                exposed_credentials.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "position": match.span(),
                    "context": context,
                    "severity": "high" if "sk-" in match.group() else "medium"
                })
                
                self.detection_log.append({
                    "type": "credential_exposure",
                    "pattern": pattern,
                    "context": context,
                    "timestamp": datetime.now()
                })
        
        return exposed_credentials
    
    def validate_api_key_format(self, api_key: str, provider: str) -> Dict[str, Any]:
        """Valide le format d'une clé API"""
        validation_result = {
            "valid_format": False,
            "provider": provider,
            "length": len(api_key),
            "contains_prefix": False,
            "entropy_score": 0.0,
            "security_issues": []
        }
        
        # Validation selon le provider
        if provider.lower() == "openai":
            # Format attendu: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            if api_key.startswith("sk-") and len(api_key) >= 51:
                validation_result["valid_format"] = True
                validation_result["contains_prefix"] = True
            else:
                validation_result["security_issues"].append("Format OpenAI invalide")
        
        elif provider.lower() == "openbb":
            # Format généralement UUID ou token long
            if len(api_key) >= 32:
                validation_result["valid_format"] = True
            else:
                validation_result["security_issues"].append("Clé OpenBB trop courte")
        
        # Calculer entropie (mesure de randomness)
        if api_key:
            unique_chars = len(set(api_key))
            validation_result["entropy_score"] = unique_chars / len(api_key)
            
            if validation_result["entropy_score"] < 0.5:
                validation_result["security_issues"].append("Entropie faible - clé potentiellement faible")
        
        return validation_result
    
    def test_credential_storage_security(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la sécurité du stockage des credentials"""
        security_issues = []
        storage_score = 1.0
        
        # Vérifier que les clés ne sont pas en dur dans le code
        exposed_creds = self.scan_for_exposed_credentials(config_data, "config")
        if exposed_creds:
            security_issues.append(f"{len(exposed_creds)} credentials exposés trouvés")
            storage_score -= 0.5
        
        # Vérifier utilisation variables d'environnement
        env_usage = 0
        total_keys = 0
        
        for key, value in config_data.items():
            if "api" in key.lower() or "key" in key.lower() or "token" in key.lower():
                total_keys += 1
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_usage += 1
                elif isinstance(value, str) and len(value) > 20:
                    # Potentielle clé en dur
                    security_issues.append(f"Clé potentiellement en dur: {key}")
                    storage_score -= 0.3
        
        env_usage_rate = env_usage / total_keys if total_keys > 0 else 1.0
        
        if env_usage_rate < 0.8:
            security_issues.append("Utilisation insuffisante des variables d'environnement")
            storage_score -= 0.2
        
        return {
            "storage_score": max(0.0, storage_score),
            "env_usage_rate": env_usage_rate,
            "security_issues": security_issues,
            "exposed_credentials": exposed_creds
        }


class APISecurityValidator:
    """Validateur de sécurité API"""
    
    def __init__(self):
        self.security_checks = []
        self.rate_limit_tracker = {}
    
    def validate_request_sanitization(self, request_data: Dict[str, Any]) -> SecurityTestResult:
        """Valide la sanitisation des requêtes"""
        blocked_patterns = SECURITY_CONFIG["blocked_patterns"]
        vulnerabilities = []
        
        # Convertir requête en string pour analyse
        request_content = json.dumps(request_data) if isinstance(request_data, dict) else str(request_data)
        
        # Chercher patterns dangereux
        for pattern in blocked_patterns:
            if re.search(pattern, request_content, re.IGNORECASE):
                vulnerabilities.append({
                    "pattern": pattern,
                    "type": "injection_attempt",
                    "content": request_content[:100] + "..." if len(request_content) > 100 else request_content
                })
        
        vulnerability_detected = len(vulnerabilities) > 0
        security_level = "low" if vulnerability_detected else "high"
        
        return SecurityTestResult(
            test_name="request_sanitization",
            security_check_type="input_validation",
            vulnerability_detected=vulnerability_detected,
            security_level=security_level,
            remediation_required=vulnerability_detected,
            compliance_score=0.0 if vulnerability_detected else 1.0
        )
    
    def test_rate_limiting(self, api_endpoint: str, requests_per_minute: int) -> SecurityTestResult:
        """Teste les limites de taux d'API"""
        rate_limit = SECURITY_CONFIG["api_rate_limit_per_minute"]
        
        # Simuler tracking de rate limit
        current_minute = datetime.now().replace(second=0, microsecond=0)
        endpoint_key = f"{api_endpoint}_{current_minute}"
        
        if endpoint_key not in self.rate_limit_tracker:
            self.rate_limit_tracker[endpoint_key] = 0
        
        self.rate_limit_tracker[endpoint_key] += requests_per_minute
        
        # Vérifier si limite dépassée
        exceeded_limit = self.rate_limit_tracker[endpoint_key] > rate_limit
        
        return SecurityTestResult(
            test_name="rate_limiting",
            security_check_type="api_protection",
            vulnerability_detected=exceeded_limit,
            security_level="low" if exceeded_limit else "high",
            remediation_required=exceeded_limit,
            compliance_score=0.0 if exceeded_limit else 1.0
        )
    
    def validate_https_usage(self, api_urls: List[str]) -> SecurityTestResult:
        """Valide l'utilisation de HTTPS"""
        non_secure_urls = []
        
        for url in api_urls:
            if not url.startswith("https://"):
                non_secure_urls.append(url)
        
        vulnerability_detected = len(non_secure_urls) > 0
        security_level = "low" if vulnerability_detected else "high"
        
        return SecurityTestResult(
            test_name="https_validation",
            security_check_type="transport_security",
            vulnerability_detected=vulnerability_detected,
            security_level=security_level,
            remediation_required=vulnerability_detected,
            compliance_score=(len(api_urls) - len(non_secure_urls)) / len(api_urls) if api_urls else 1.0
        )


@pytest.mark.security
@pytest.mark.api_security
class TestBasicAPISecurity:
    """Tests de sécurité API de base"""
    
    @pytest.fixture
    def security_test_config(self):
        """Configuration pour tests de sécurité"""
        return {
            "openai": {
                "api_key": "${OPENAI_API_KEY}",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30
            },
            "openbb": {
                "api_key": "${OPENBB_API_KEY}", 
                "base_url": "https://api.openbb.co/v1",
                "timeout": 30
            }
        }
    
    def test_credential_protection(self, security_test_config):
        """Test protection des credentials"""
        credential_tester = CredentialProtectionTester()
        
        print("🔐 Test protection credentials")
        
        # Test stockage sécurisé
        storage_result = credential_tester.test_credential_storage_security(security_test_config)
        
        print(f"   Score stockage: {storage_result['storage_score']:.2f}")
        print(f"   Utilisation env vars: {storage_result['env_usage_rate']:.1%}")
        print(f"   Issues sécurité: {len(storage_result['security_issues'])}")
        
        for issue in storage_result['security_issues']:
            print(f"      ⚠️  {issue}")
        
        # Test validation format clés API
        test_api_keys = {
            "openai_valid": "sk-" + "x" * 48,
            "openai_invalid": "invalid_key",
            "openbb_valid": "bb_" + "x" * 32,
            "openbb_invalid": "short"
        }
        
        validation_results = {}
        
        for key_name, api_key in test_api_keys.items():
            provider = "openai" if "openai" in key_name else "openbb"
            validation = credential_tester.validate_api_key_format(api_key, provider)
            validation_results[key_name] = validation
            
            print(f"   {key_name}: {'✓' if validation['valid_format'] else '✗'} "
                  f"(entropie: {validation['entropy_score']:.2f})")
        
        # Assertions protection credentials
        assert storage_result['storage_score'] >= 0.8  # Au moins 80% sécurisé
        assert storage_result['env_usage_rate'] >= 0.5  # Au moins 50% env vars
        assert len(storage_result['exposed_credentials']) == 0  # Pas de credentials exposés
        
        # Vérifier format clés valides
        assert validation_results['openai_valid']['valid_format']
        assert validation_results['openbb_valid']['valid_format']
        assert not validation_results['openai_invalid']['valid_format']
        assert not validation_results['openbb_invalid']['valid_format']
        
        return {
            "storage_result": storage_result,
            "validation_results": validation_results
        }
    
    @pytest.mark.asyncio
    async def test_api_request_security(self, security_test_config):
        """Test sécurité des requêtes API"""
        security_validator = APISecurityValidator()
        
        print("🌐 Test sécurité requêtes API")
        
        # Test requêtes légitimes
        legitimate_requests = [
            {"symbol": "AAPL", "period": "1d"},
            {"query": "market analysis", "max_tokens": 1000},
            {"portfolio_id": "12345", "action": "get_value"}
        ]
        
        legitimate_results = []
        for i, request in enumerate(legitimate_requests):
            result = security_validator.validate_request_sanitization(request)
            legitimate_results.append(result)
            print(f"   Requête {i+1}: {'✓' if not result.vulnerability_detected else '✗'}")
        
        # Test requêtes malicieuses
        malicious_requests = [
            {"symbol": "<script>alert('xss')</script>"},
            {"query": "'; DROP TABLE users; --"},
            {"data": "javascript:alert('malicious')"},
            {"input": "union select * from secrets"}
        ]
        
        malicious_results = []
        for i, request in enumerate(malicious_requests):
            result = security_validator.validate_request_sanitization(request)
            malicious_results.append(result)
            print(f"   Malicieux {i+1}: {'🔴' if result.vulnerability_detected else '✓'} "
                  f"(détection: {'oui' if result.vulnerability_detected else 'non'})")
        
        # Test URLs HTTPS
        api_urls = [
            "https://api.openai.com/v1/chat/completions",
            "https://api.openbb.co/v1/equity/price",
            "http://insecure-api.com/data"  # URL non sécurisée
        ]
        
        https_result = security_validator.validate_https_usage(api_urls)
        print(f"   HTTPS compliance: {https_result.compliance_score:.1%}")
        
        # Test rate limiting
        rate_limit_result = security_validator.test_rate_limiting("test_endpoint", 100)  # > limite
        print(f"   Rate limit: {'✓' if not rate_limit_result.vulnerability_detected else '🔴'}")
        
        # Calculer score sécurité global
        all_results = legitimate_results + malicious_results + [https_result, rate_limit_result]
        security_score = sum(r.compliance_score for r in all_results) / len(all_results)
        
        print(f"\n📊 Score sécurité API global: {security_score:.2f}")
        
        # Assertions sécurité API
        assert all(not r.vulnerability_detected for r in legitimate_results)  # Requêtes légitimes OK
        assert sum(r.vulnerability_detected for r in malicious_results) >= 3  # Au moins 3 détections
        assert https_result.compliance_score >= 0.6  # Au moins 60% HTTPS
        
        return {
            "legitimate_results": legitimate_results,
            "malicious_results": malicious_results,
            "https_result": https_result,
            "rate_limit_result": rate_limit_result,
            "security_score": security_score
        }
    
    def test_environment_variable_security(self):
        """Test sécurité des variables d'environnement"""
        print("🌍 Test sécurité variables d'environnement")
        
        # Simuler variables d'environnement
        test_env_vars = {
            "OPENAI_API_KEY": "sk-" + "x" * 48,
            "OPENBB_API_KEY": "bb_" + "x" * 32,
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "SECRET_KEY": "very_secret_key_123",
            "DEBUG": "False"
        }
        
        # Analyser sécurité
        credential_tester = CredentialProtectionTester()
        security_issues = []
        
        for var_name, var_value in test_env_vars.items():
            # Vérifier que variables sensibles ne sont pas exposées
            if any(keyword in var_name.upper() for keyword in ["KEY", "SECRET", "TOKEN", "PASSWORD"]):
                if len(var_value) < 16:
                    security_issues.append(f"Variable {var_name} trop courte")
                
                # Vérifier pattern de sécurité
                validation = credential_tester.validate_api_key_format(
                    var_value, 
                    "openai" if "OPENAI" in var_name else "generic"
                )
                
                if validation["entropy_score"] < 0.5:
                    security_issues.append(f"Entropie faible pour {var_name}")
        
        # Test accès sécurisé aux variables
        def secure_env_access(var_name: str, default: str = None) -> Optional[str]:
            """Accès sécurisé aux variables d'environnement"""
            try:
                value = test_env_vars.get(var_name, default)
                if value and any(keyword in var_name.upper() for keyword in ["KEY", "SECRET", "TOKEN"]):
                    # Log accès à variable sensible
                    print(f"      Accès sécurisé à {var_name}")
                return value
            except Exception as e:
                print(f"      Erreur accès {var_name}: {e}")
                return default
        
        # Test accès
        openai_key = secure_env_access("OPENAI_API_KEY")
        openbb_key = secure_env_access("OPENBB_API_KEY")
        debug_flag = secure_env_access("DEBUG", "False")
        
        env_security_score = max(0.0, 1.0 - (len(security_issues) * 0.2))
        
        print(f"   Variables testées: {len(test_env_vars)}")
        print(f"   Issues sécurité: {len(security_issues)}")
        print(f"   Score sécurité env: {env_security_score:.2f}")
        
        for issue in security_issues:
            print(f"      ⚠️  {issue}")
        
        # Assertions sécurité environnement
        assert env_security_score >= 0.6  # Au moins 60% sécurisé
        assert openai_key is not None  # Accès réussi
        assert openbb_key is not None  # Accès réussi
        
        return {
            "security_issues": security_issues,
            "env_security_score": env_security_score,
            "tested_vars": len(test_env_vars)
        }


@pytest.mark.security
@pytest.mark.api_security
@pytest.mark.slow
class TestAdvancedAPISecurity:
    """Tests avancés de sécurité API"""
    
    @pytest.mark.asyncio
    async def test_api_authentication_security(self):
        """Test sécurité de l'authentification API"""
        print("🔑 Test sécurité authentification API")
        
        # Simuler différents scénarios d'authentification
        auth_scenarios = [
            {
                "name": "valid_api_key",
                "headers": {"Authorization": "Bearer sk-valid_key_here"},
                "should_pass": True
            },
            {
                "name": "missing_auth",
                "headers": {},
                "should_pass": False
            },
            {
                "name": "invalid_format",
                "headers": {"Authorization": "InvalidFormat"},
                "should_pass": False
            },
            {
                "name": "expired_token",
                "headers": {"Authorization": "Bearer expired_token"},
                "should_pass": False
            }
        ]
        
        auth_results = {}
        
        for scenario in auth_scenarios:
            scenario_name = scenario["name"]
            headers = scenario["headers"]
            expected_pass = scenario["should_pass"]
            
            # Simuler validation authentification
            auth_valid = False
            if "Authorization" in headers:
                auth_header = headers["Authorization"]
                if auth_header.startswith("Bearer ") and len(auth_header) > 20:
                    if "valid_key" in auth_header or "sk-" in auth_header:
                        auth_valid = True
            
            auth_results[scenario_name] = {
                "auth_provided": "Authorization" in headers,
                "auth_valid": auth_valid,
                "expected_pass": expected_pass,
                "test_passed": auth_valid == expected_pass
            }
            
            status = "✓" if auth_results[scenario_name]["test_passed"] else "✗"
            print(f"   {scenario_name}: {status} "
                  f"(auth: {'oui' if auth_valid else 'non'}, "
                  f"attendu: {'pass' if expected_pass else 'fail'})")
        
        # Calculer score authentification
        passed_tests = sum(1 for r in auth_results.values() if r["test_passed"])
        auth_score = passed_tests / len(auth_scenarios)
        
        print(f"\n📊 Score authentification: {auth_score:.2f}")
        
        # Assertions authentification
        assert auth_score >= 0.8  # Au moins 80% des tests passent
        assert auth_results["valid_api_key"]["auth_valid"]  # Clé valide acceptée
        assert not auth_results["missing_auth"]["auth_valid"]  # Auth manquante rejetée
        
        return {
            "auth_results": auth_results,
            "auth_score": auth_score
        }
    
    def test_sensitive_data_masking(self):
        """Test masquage des données sensibles"""
        print("🎭 Test masquage données sensibles")
        
        def mask_sensitive_data(data: str) -> str:
            """Masque les données sensibles"""
            # Masquer clés API
            data = re.sub(r'(sk-)[a-zA-Z0-9]{32,}', r'\1***MASKED***', data)
            
            # Masquer tokens
            data = re.sub(r'([a-zA-Z0-9]{24,})', lambda m: m.group(1)[:8] + '***' + m.group(1)[-4:] if len(m.group(1)) > 12 else m.group(1), data)
            
            # Masquer emails
            data = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'***@\2', data)
            
            return data
        
        # Test données avec informations sensibles
        test_data = [
            "API Key: sk-1234567890abcdef1234567890abcdef12345678",
            "Token: abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
            "Email: user@example.com",
            "Normal data without sensitive info",
            "Mixed: sk-secretkey123456789012345678901234567890 and user@test.com"
        ]
        
        masking_results = {}
        
        for i, original_data in enumerate(test_data):
            masked_data = mask_sensitive_data(original_data)
            
            # Vérifier efficacité du masquage
            contains_api_key = "sk-" in masked_data and len(re.findall(r'sk-[a-zA-Z0-9]{32,}', masked_data)) > 0
            contains_full_email = "@" in masked_data and re.search(r'[a-zA-Z0-9._%+-]+@', masked_data)
            
            masking_effective = not contains_api_key and not contains_full_email
            
            masking_results[f"test_{i+1}"] = {
                "original": original_data,
                "masked": masked_data,
                "masking_effective": masking_effective,
                "reduction_ratio": 1.0 - (len(masked_data) / len(original_data)) if original_data else 0.0
            }
            
            print(f"   Test {i+1}: {'✓' if masking_effective else '✗'}")
            print(f"      Original: {original_data[:50]}...")
            print(f"      Masqué:   {masked_data[:50]}...")
        
        # Calculer efficacité globale
        effective_maskings = sum(1 for r in masking_results.values() if r["masking_effective"])
        masking_score = effective_maskings / len(masking_results)
        
        print(f"\n📊 Score masquage: {masking_score:.2f}")
        
        # Assertions masquage
        assert masking_score >= 0.8  # Au moins 80% efficace
        
        return {
            "masking_results": masking_results,
            "masking_score": masking_score
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "api_security and not slow"])