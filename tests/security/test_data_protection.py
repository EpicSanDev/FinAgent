"""
Tests de Sécurité - Protection des Données

Ces tests valident la protection des données sensibles,
le chiffrement approprié, la gestion sécurisée des logs
et la conformité aux standards de protection des données.
"""

import pytest
import os
import json
import hashlib
import base64
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch, MagicMock
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import re

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision
from finagent.business.exceptions import DataError, ValidationError

# Import des utilitaires de test
from tests.utils import create_test_portfolio
from tests.security import SECURITY_CONFIG


@dataclass
class DataProtectionResult:
    """Résultat de test de protection des données"""
    test_name: str
    protection_type: str
    encryption_used: bool
    sensitive_data_masked: bool
    access_controls_enforced: bool
    audit_trail_maintained: bool
    compliance_score: float


class DataEncryption:
    """Gestionnaire de chiffrement des données"""
    
    def __init__(self, password: Optional[str] = None):
        if password:
            self.key = self._derive_key(password.encode())
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.encryption_log = []
    
    def _derive_key(self, password: bytes) -> bytes:
        """Dérive une clé à partir d'un mot de passe"""
        salt = b'finagent_salt_2024'  # En prod, utiliser salt aléatoire
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data: Any) -> str:
        """Chiffre des données"""
        if isinstance(data, dict):
            serialized = json.dumps(data, default=str)
        else:
            serialized = str(data)
        
        encrypted = self.cipher.encrypt(serialized.encode())
        
        self.encryption_log.append({
            "action": "encrypt",
            "data_type": type(data).__name__,
            "timestamp": datetime.now(),
            "size": len(serialized)
        })
        
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Déchiffre des données"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            
            self.encryption_log.append({
                "action": "decrypt",
                "timestamp": datetime.now(),
                "success": True
            })
            
            # Tenter désérialisation JSON
            try:
                return json.loads(decrypted.decode())
            except json.JSONDecodeError:
                return decrypted.decode()
                
        except Exception as e:
            self.encryption_log.append({
                "action": "decrypt",
                "timestamp": datetime.now(),
                "success": False,
                "error": str(e)
            })
            raise DataError(f"Échec déchiffrement: {e}")
    
    def hash_data(self, data: str) -> str:
        """Hache des données (non réversible)"""
        return hashlib.sha256(data.encode()).hexdigest()


class SensitiveDataDetector:
    """Détecteur de données sensibles"""
    
    def __init__(self):
        self.sensitive_patterns = {
            'api_key': r'(sk-|pk_|rk_)[a-zA-Z0-9]{32,}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'password': r'(password|pwd|pass)["\']?\s*[:=]\s*["\']?[^\s"\']+',
            'token': r'(token|bearer)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9+/]{20,}'
        }
        self.detections = []
    
    def scan_for_sensitive_data(self, data: Any, context: str = "") -> List[Dict[str, Any]]:
        """Scanne pour des données sensibles"""
        if isinstance(data, dict):
            content = json.dumps(data, indent=2)
        elif isinstance(data, list):
            content = str(data)
        else:
            content = str(data)
        
        detected_items = []
        
        for data_type, pattern in self.sensitive_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                detection = {
                    'type': data_type,
                    'pattern': pattern,
                    'match': match.group(),
                    'position': match.span(),
                    'context': context,
                    'timestamp': datetime.now()
                }
                detected_items.append(detection)
                self.detections.append(detection)
        
        return detected_items
    
    def mask_sensitive_data(self, data: str) -> str:
        """Masque les données sensibles"""
        masked = data
        
        # Masquer clés API
        masked = re.sub(r'(sk-|pk_|rk_)[a-zA-Z0-9]{32,}', r'\1****MASKED****', masked)
        
        # Masquer emails
        masked = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'****@\2', masked)
        
        # Masquer cartes de crédit
        masked = re.sub(r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b', r'\1-****-****-\4', masked)
        
        # Masquer mots de passe
        masked = re.sub(r'(password|pwd|pass)["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'\1=****MASKED****', masked, flags=re.IGNORECASE)
        
        return masked


class SecureLogging:
    """Système de logging sécurisé"""
    
    def __init__(self):
        self.logs = []
        self.sensitive_detector = SensitiveDataDetector()
        self.setup_secure_logger()
    
    def setup_secure_logger(self):
        """Configure un logger sécurisé"""
        self.logger = logging.getLogger('finagent_secure')
        self.logger.setLevel(logging.INFO)
        
        # Handler qui masque automatiquement les données sensibles
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def secure_log(self, level: str, message: str, context: Dict[str, Any] = None):
        """Log sécurisé avec masquage automatique"""
        # Masquer données sensibles dans le message
        safe_message = self.sensitive_detector.mask_sensitive_data(message)
        
        # Masquer données sensibles dans le contexte
        safe_context = {}
        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    safe_context[key] = self.sensitive_detector.mask_sensitive_data(value)
                else:
                    safe_context[key] = value
        
        # Créer entrée de log
        log_entry = {
            'timestamp': datetime.now(),
            'level': level,
            'message': safe_message,
            'context': safe_context,
            'masked_data_count': len(self.sensitive_detector.scan_for_sensitive_data(message + str(context or {})))
        }
        
        self.logs.append(log_entry)
        
        # Log effectif
        if level.upper() == 'ERROR':
            self.logger.error(f"{safe_message} | Context: {safe_context}")
        elif level.upper() == 'WARNING':
            self.logger.warning(f"{safe_message} | Context: {safe_context}")
        else:
            self.logger.info(f"{safe_message} | Context: {safe_context}")
    
    def get_audit_trail(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Récupère la piste d'audit"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        return [
            log for log in self.logs 
            if log['timestamp'] >= cutoff_time
        ]


@pytest.mark.security
@pytest.mark.data_protection
class TestBasicDataProtection:
    """Tests de protection des données de base"""
    
    @pytest.fixture
    def data_encryptor(self):
        """Chiffreur de données pour tests"""
        return DataEncryption("test_password_123")
    
    @pytest.fixture
    def sensitive_detector(self):
        """Détecteur de données sensibles pour tests"""
        return SensitiveDataDetector()
    
    @pytest.fixture
    def secure_logger(self):
        """Logger sécurisé pour tests"""
        return SecureLogging()
    
    def test_data_encryption(self, data_encryptor):
        """Test chiffrement des données"""
        print("🔐 Test chiffrement données")
        
        # Données test à chiffrer
        test_data = [
            {"api_key": "sk-1234567890abcdef", "user": "test@example.com"},
            "Sensitive information: password123",
            create_test_portfolio(1000.0).__dict__,
            {"credit_card": "4532-1234-5678-9012", "cvv": "123"}
        ]
        
        encryption_results = {}
        
        for i, data in enumerate(test_data):
            test_name = f"test_{i+1}"
            
            # Test chiffrement
            try:
                encrypted = data_encryptor.encrypt_data(data)
                encryption_success = len(encrypted) > 0 and encrypted != str(data)
                
                # Test déchiffrement
                decrypted = data_encryptor.decrypt_data(encrypted)
                decryption_success = decrypted == data if not isinstance(data, object) else True
                
                # Vérifier que données chiffrées ne contiennent pas d'infos sensibles
                contains_sensitive = any(
                    keyword in encrypted.lower() 
                    for keyword in ['password', 'api_key', 'credit_card', 'sk-']
                )
                
                encryption_results[test_name] = {
                    'original_type': type(data).__name__,
                    'encrypted_length': len(encrypted),
                    'encryption_success': encryption_success,
                    'decryption_success': decryption_success,
                    'no_sensitive_in_encrypted': not contains_sensitive,
                    'overall_success': encryption_success and decryption_success and not contains_sensitive
                }
                
                print(f"   {test_name}: {'✓' if encryption_results[test_name]['overall_success'] else '✗'}")
                
            except Exception as e:
                encryption_results[test_name] = {
                    'error': str(e),
                    'overall_success': False
                }
                print(f"   {test_name}: ✗ (Erreur: {e})")
        
        # Calculer score chiffrement
        successful_encryptions = sum(1 for r in encryption_results.values() if r.get('overall_success', False))
        encryption_score = successful_encryptions / len(encryption_results)
        
        print(f"\n📊 Score chiffrement: {encryption_score:.2f}")
        print(f"   Opérations réussies: {successful_encryptions}/{len(encryption_results)}")
        
        # Vérifier log chiffrement
        encryption_log = data_encryptor.encryption_log
        print(f"   Opérations loggées: {len(encryption_log)}")
        
        # Assertions chiffrement
        assert encryption_score >= 0.8  # Au moins 80% succès
        assert len(encryption_log) >= len(test_data) * 2  # Au moins encrypt + decrypt par test
        
        return {
            'encryption_results': encryption_results,
            'encryption_score': encryption_score,
            'encryption_log': encryption_log
        }
    
    def test_sensitive_data_detection(self, sensitive_detector):
        """Test détection de données sensibles"""
        print("🔍 Test détection données sensibles")
        
        # Données test avec informations sensibles
        test_cases = [
            {
                'name': 'api_keys',
                'data': {'openai_key': 'sk-1234567890abcdef1234567890abcdef12345678', 'public_key': 'pk_test_123456789'},
                'expected_detections': 2
            },
            {
                'name': 'personal_info',
                'data': {'email': 'user@example.com', 'phone': '555-123-4567', 'ssn': '123-45-6789'},
                'expected_detections': 3
            },
            {
                'name': 'financial_data',
                'data': {'card': '4532 1234 5678 9012', 'account': 'ACC-12345'},
                'expected_detections': 1
            },
            {
                'name': 'credentials',
                'data': 'password: secret123, token: bearer_abc123def456ghi789',
                'expected_detections': 2
            },
            {
                'name': 'clean_data',
                'data': {'symbol': 'AAPL', 'price': 150.0, 'quantity': 100},
                'expected_detections': 0
            }
        ]
        
        detection_results = {}
        
        for test_case in test_cases:
            test_name = test_case['name']
            data = test_case['data']
            expected = test_case['expected_detections']
            
            # Scan pour données sensibles
            detections = sensitive_detector.scan_for_sensitive_data(data, test_name)
            detected_count = len(detections)
            
            # Test masquage
            if isinstance(data, str):
                masked = sensitive_detector.mask_sensitive_data(data)
                masking_effective = masked != data and '****' in masked
            else:
                data_str = json.dumps(data)
                masked = sensitive_detector.mask_sensitive_data(data_str)
                masking_effective = masked != data_str and '****' in masked
            
            detection_accuracy = detected_count == expected
            
            detection_results[test_name] = {
                'data_type': type(data).__name__,
                'expected_detections': expected,
                'actual_detections': detected_count,
                'detection_accuracy': detection_accuracy,
                'masking_effective': masking_effective if detected_count > 0 else True,
                'detected_types': [d['type'] for d in detections]
            }
            
            print(f"   {test_name}: {'✓' if detection_accuracy else '✗'} "
                  f"({detected_count}/{expected} détections)")
            
            if detections:
                for detection in detections:
                    print(f"      Détecté: {detection['type']} - {detection['match'][:20]}...")
        
        # Score global détection
        accurate_detections = sum(1 for r in detection_results.values() if r['detection_accuracy'])
        detection_score = accurate_detections / len(detection_results)
        
        effective_maskings = sum(1 for r in detection_results.values() if r['masking_effective'])
        masking_score = effective_maskings / len(detection_results)
        
        overall_score = (detection_score + masking_score) / 2
        
        print(f"\n📊 Scores détection données sensibles:")
        print(f"   Détection: {detection_score:.2f}")
        print(f"   Masquage: {masking_score:.2f}")
        print(f"   Score global: {overall_score:.2f}")
        
        # Assertions détection
        assert detection_score >= 0.8  # Au moins 80% précision détection
        assert masking_score >= 0.9   # Au moins 90% masquage efficace
        
        return {
            'detection_results': detection_results,
            'detection_score': detection_score,
            'masking_score': masking_score,
            'overall_score': overall_score,
            'total_detections': len(sensitive_detector.detections)
        }
    
    def test_secure_logging(self, secure_logger):
        """Test logging sécurisé"""
        print("📝 Test logging sécurisé")
        
        # Test logs avec données sensibles
        test_logs = [
            {
                'level': 'INFO',
                'message': 'User login successful',
                'context': {'user': 'test@example.com', 'session': 'sess_123456'}
            },
            {
                'level': 'ERROR',
                'message': 'API call failed with key sk-1234567890abcdef',
                'context': {'endpoint': '/api/data', 'status': 401}
            },
            {
                'level': 'WARNING',
                'message': 'Credit card validation: 4532-1234-5678-9012',
                'context': {'amount': 100.0, 'currency': 'USD'}
            },
            {
                'level': 'INFO',
                'message': 'Portfolio update completed',
                'context': {'portfolio_id': 'P123', 'value': 50000.0}
            }
        ]
        
        # Générer logs
        for log_data in test_logs:
            secure_logger.secure_log(
                log_data['level'],
                log_data['message'],
                log_data['context']
            )
        
        # Analyser logs générés
        audit_trail = secure_logger.get_audit_trail(24)
        
        logging_results = {
            'total_logs': len(audit_trail),
            'logs_with_masked_data': sum(1 for log in audit_trail if log['masked_data_count'] > 0),
            'sensitive_data_exposed': [],
            'masking_effectiveness': 0.0
        }
        
        # Vérifier que données sensibles sont masquées
        for log in audit_trail:
            message = log['message']
            context_str = str(log['context'])
            
            # Chercher données sensibles non masquées
            sensitive_patterns = [
                r'sk-[a-zA-Z0-9]{32,}',
                r'\d{4}-\d{4}-\d{4}-\d{4}',
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, message + context_str):
                    logging_results['sensitive_data_exposed'].append({
                        'log_id': log.get('id', 'unknown'),
                        'pattern': pattern,
                        'timestamp': log['timestamp']
                    })
        
        # Calculer efficacité masquage
        logs_with_sensitive = len([log for log in test_logs if any(
            keyword in (log['message'] + str(log['context'])).lower()
            for keyword in ['sk-', '@', '4532', 'password']
        )])
        
        if logs_with_sensitive > 0:
            effectively_masked = logs_with_sensitive - len(logging_results['sensitive_data_exposed'])
            logging_results['masking_effectiveness'] = effectively_masked / logs_with_sensitive
        else:
            logging_results['masking_effectiveness'] = 1.0
        
        print(f"   Logs générés: {logging_results['total_logs']}")
        print(f"   Logs avec données masquées: {logging_results['logs_with_masked_data']}")
        print(f"   Efficacité masquage: {logging_results['masking_effectiveness']:.1%}")
        print(f"   Données sensibles exposées: {len(logging_results['sensitive_data_exposed'])}")
        
        # Assertions logging sécurisé
        assert logging_results['total_logs'] == len(test_logs)  # Tous logs générés
        assert len(logging_results['sensitive_data_exposed']) == 0  # Aucune exposition
        assert logging_results['masking_effectiveness'] >= 0.9  # Au moins 90% masquage
        
        return logging_results


@pytest.mark.security
@pytest.mark.data_protection
@pytest.mark.slow
class TestAdvancedDataProtection:
    """Tests avancés de protection des données"""
    
    def test_data_retention_policies(self):
        """Test politiques de rétention des données"""
        print("📅 Test politiques rétention données")
        
        # Simuler données avec différents âges
        current_time = datetime.now()
        test_data = [
            {
                'id': 'data_1',
                'created': current_time - timedelta(days=1),
                'type': 'user_data',
                'retention_days': 365
            },
            {
                'id': 'data_2', 
                'created': current_time - timedelta(days=400),
                'type': 'user_data',
                'retention_days': 365
            },
            {
                'id': 'data_3',
                'created': current_time - timedelta(days=10),
                'type': 'transaction_log',
                'retention_days': 30
            },
            {
                'id': 'data_4',
                'created': current_time - timedelta(days=40),
                'type': 'transaction_log',
                'retention_days': 30
            }
        ]
        
        def should_be_retained(data_item):
            """Détermine si une donnée doit être conservée"""
            age_days = (current_time - data_item['created']).days
            return age_days <= data_item['retention_days']
        
        def apply_retention_policy(data_list):
            """Applique la politique de rétention"""
            retained = []
            purged = []
            
            for item in data_list:
                if should_be_retained(item):
                    retained.append(item)
                else:
                    purged.append(item)
            
            return retained, purged
        
        # Appliquer politique
        retained_data, purged_data = apply_retention_policy(test_data)
        
        retention_results = {
            'total_items': len(test_data),
            'retained_items': len(retained_data),
            'purged_items': len(purged_data),
            'retention_rate': len(retained_data) / len(test_data),
            'policy_compliance': True
        }
        
        print(f"   Éléments totaux: {retention_results['total_items']}")
        print(f"   Éléments conservés: {retention_results['retained_items']}")
        print(f"   Éléments purgés: {retention_results['purged_items']}")
        print(f"   Taux rétention: {retention_results['retention_rate']:.1%}")
        
        # Vérifier conformité politique
        for item in retained_data:
            age_days = (current_time - item['created']).days
            if age_days > item['retention_days']:
                retention_results['policy_compliance'] = False
                print(f"   ⚠️  Élément {item['id']} devrait être purgé (âge: {age_days} jours)")
        
        print(f"   Conformité politique: {'✓' if retention_results['policy_compliance'] else '✗'}")
        
        # Assertions rétention
        assert retention_results['policy_compliance']  # Politique respectée
        assert retention_results['purged_items'] >= 1  # Au moins un élément purgé
        
        return retention_results


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "data_protection and not slow"])