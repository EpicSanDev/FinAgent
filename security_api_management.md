# Sécurité et Gestion des Clés API - Agent IA Financier

## Vue d'Ensemble

La sécurité est cruciale pour un agent financier gérant des données sensibles et utilisant des APIs externes. Ce système garantit la protection des clés API, le chiffrement des données et la conformité aux bonnes pratiques de sécurité.

## 1. Architecture de Sécurité

### Modèle de Sécurité en Couches
```
┌─────────────────────────────────────────────────────────┐
│                  Application Security                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Input       │  │ Session     │  │ Rate        │     │
│  │ Validation  │  │ Management  │  │ Limiting    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Data Security                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Encryption  │  │ Key         │  │ Access      │     │
│  │ at Rest     │  │ Management  │  │ Control     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                Transport Security                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ TLS/HTTPS   │  │ Certificate │  │ API Token   │     │
│  │ Encryption  │  │ Validation  │  │ Security    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Security                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ OS          │  │ File System │  │ Network     │     │
│  │ Hardening   │  │ Permissions │  │ Security    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 2. Gestion des Clés API et Secrets

### Système de Gestion de Secrets
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring
import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path

class SecretManager:
    """Gestionnaire centralisé des secrets et clés API"""
    
    def __init__(self, service_name: str = "finagent"):
        self.service_name = service_name
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Récupère ou crée une clé de chiffrement maître"""
        try:
            # Tente de récupérer depuis le keyring du système
            key_b64 = keyring.get_password(self.service_name, "master_key")
            if key_b64:
                return base64.urlsafe_b64decode(key_b64.encode())
        except Exception:
            pass
        
        # Génère une nouvelle clé si aucune n'existe
        key = Fernet.generate_key()
        try:
            keyring.set_password(
                self.service_name, 
                "master_key", 
                base64.urlsafe_b64encode(key).decode()
            )
        except Exception:
            # Fallback vers un fichier sécurisé si keyring échoue
            self._save_key_to_file(key)
        
        return key
    
    def _save_key_to_file(self, key: bytes):
        """Sauvegarde la clé dans un fichier sécurisé"""
        key_file = Path.home() / ".finagent" / "keys" / "master.key"
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(key_file, "wb") as f:
            f.write(key)
        
        # Définit les permissions restrictives (Unix seulement)
        if os.name == 'posix':
            os.chmod(key_file, 0o600)
    
    def store_secret(self, key: str, value: str) -> None:
        """Stocke un secret de manière chiffrée"""
        encrypted_value = self.cipher_suite.encrypt(value.encode())
        encoded_value = base64.urlsafe_b64encode(encrypted_value).decode()
        
        try:
            keyring.set_password(self.service_name, key, encoded_value)
        except Exception:
            # Fallback vers fichier chiffré
            self._save_secret_to_file(key, encoded_value)
    
    def get_secret(self, key: str) -> Optional[str]:
        """Récupère un secret déchiffré"""
        try:
            encoded_value = keyring.get_password(self.service_name, key)
            if not encoded_value:
                # Tente de récupérer depuis le fichier
                encoded_value = self._load_secret_from_file(key)
            
            if encoded_value:
                encrypted_value = base64.urlsafe_b64decode(encoded_value.encode())
                decrypted_value = self.cipher_suite.decrypt(encrypted_value)
                return decrypted_value.decode()
        except Exception as e:
            logger.error(f"Failed to retrieve secret {key}: {e}")
        
        return None
    
    def delete_secret(self, key: str) -> bool:
        """Supprime un secret"""
        try:
            keyring.delete_password(self.service_name, key)
            self._delete_secret_file(key)
            return True
        except Exception:
            return False
    
    def list_secrets(self) -> List[str]:
        """Liste les clés de secrets disponibles"""
        # Note: keyring ne supporte pas nativement le listing
        # Implémentation basée sur les fichiers pour le fallback
        secrets_dir = Path.home() / ".finagent" / "secrets"
        if secrets_dir.exists():
            return [f.stem for f in secrets_dir.glob("*.enc")]
        return []

class APIKeyManager:
    """Gestionnaire spécialisé pour les clés API"""
    
    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
        self.api_configs = {
            "openbb": {
                "key_name": "openbb_api_key",
                "required": True,
                "description": "Clé API OpenBB pour données financières"
            },
            "openrouter": {
                "key_name": "openrouter_api_key", 
                "required": True,
                "description": "Clé API OpenRouter pour Claude"
            },
            "alpha_vantage": {
                "key_name": "alpha_vantage_api_key",
                "required": False,
                "description": "Clé API Alpha Vantage (backup)"
            }
        }
    
    def setup_api_key(self, service: str, api_key: str) -> bool:
        """Configure une clé API pour un service"""
        if service not in self.api_configs:
            raise ValueError(f"Unknown service: {service}")
        
        # Valide le format de la clé
        if not self._validate_api_key_format(service, api_key):
            raise ValueError(f"Invalid API key format for {service}")
        
        key_name = self.api_configs[service]["key_name"]
        self.secret_manager.store_secret(key_name, api_key)
        
        # Teste la clé
        return self._test_api_key(service, api_key)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Récupère une clé API"""
        if service not in self.api_configs:
            return None
        
        key_name = self.api_configs[service]["key_name"]
        return self.secret_manager.get_secret(key_name)
    
    def validate_all_keys(self) -> Dict[str, bool]:
        """Valide toutes les clés API configurées"""
        results = {}
        
        for service, config in self.api_configs.items():
            api_key = self.get_api_key(service)
            if api_key:
                results[service] = self._test_api_key(service, api_key)
            elif config["required"]:
                results[service] = False
            else:
                results[service] = None  # Optionnel, non configuré
        
        return results
    
    def _validate_api_key_format(self, service: str, api_key: str) -> bool:
        """Valide le format d'une clé API"""
        if not api_key or len(api_key) < 10:
            return False
        
        # Validations spécifiques par service
        if service == "openbb":
            return len(api_key) >= 32 and api_key.replace("-", "").isalnum()
        elif service == "openrouter":
            return api_key.startswith("sk-or-") and len(api_key) > 20
        elif service == "alpha_vantage":
            return len(api_key) >= 16 and api_key.isalnum()
        
        return True
    
    async def _test_api_key(self, service: str, api_key: str) -> bool:
        """Teste une clé API"""
        try:
            if service == "openbb":
                return await self._test_openbb_key(api_key)
            elif service == "openrouter":
                return await self._test_openrouter_key(api_key)
            elif service == "alpha_vantage":
                return await self._test_alpha_vantage_key(api_key)
        except Exception as e:
            logger.warning(f"API key test failed for {service}: {e}")
            return False
        
        return False
```

## 3. Chiffrement des Données

### Système de Chiffrement Multi-Couches
```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.backends import default_backend
import secrets
from typing import Tuple

class DataEncryption:
    """Système de chiffrement pour données sensibles"""
    
    def __init__(self, master_key: bytes):
        self.master_key = master_key
        
    def encrypt_data(self, data: bytes) -> Tuple[bytes, bytes, bytes]:
        """Chiffre des données avec AES-256-CBC"""
        # Génère une clé dérivée unique pour cette opération
        salt = secrets.token_bytes(16)
        derived_key = self._derive_key(self.master_key, salt)
        
        # Génère un IV aléatoire
        iv = secrets.token_bytes(16)
        
        # Padding PKCS7
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Chiffrement AES-256-CBC
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data, salt, iv
    
    def decrypt_data(self, encrypted_data: bytes, salt: bytes, iv: bytes) -> bytes:
        """Déchiffre des données"""
        # Dérive la même clé
        derived_key = self._derive_key(self.master_key, salt)
        
        # Déchiffrement
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Retire le padding
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
    
    def _derive_key(self, master_key: bytes, salt: bytes) -> bytes:
        """Dérive une clé à partir de la clé maître"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits pour AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(master_key)

class FieldLevelEncryption:
    """Chiffrement au niveau des champs pour la base de données"""
    
    def __init__(self, encryption_service: DataEncryption):
        self.encryption = encryption_service
        self.encrypted_fields = {
            "api_keys",
            "personal_data", 
            "financial_data",
            "strategy_configs"
        }
    
    def encrypt_field(self, field_name: str, value: str) -> Optional[str]:
        """Chiffre un champ si nécessaire"""
        if field_name not in self.encrypted_fields:
            return value
        
        if value is None:
            return None
        
        encrypted_data, salt, iv = self.encryption.encrypt_data(value.encode())
        
        # Combine tout en base64 pour stockage en DB
        combined = salt + iv + encrypted_data
        return base64.urlsafe_b64encode(combined).decode()
    
    def decrypt_field(self, field_name: str, encrypted_value: str) -> Optional[str]:
        """Déchiffre un champ si nécessaire"""
        if field_name not in self.encrypted_fields:
            return encrypted_value
        
        if encrypted_value is None:
            return None
        
        try:
            combined = base64.urlsafe_b64decode(encrypted_value.encode())
            salt = combined[:16]
            iv = combined[16:32]
            encrypted_data = combined[32:]
            
            decrypted_data = self.encryption.decrypt_data(encrypted_data, salt, iv)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt field {field_name}: {e}")
            return None
```

## 4. Authentification et Autorisation

### Système d'Authentification Local
```python
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class UserAuthenticator:
    """Système d'authentification pour utilisateur local"""
    
    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
        self.session_manager = SessionManager()
        
    def setup_user_credentials(self, username: str, password: str) -> bool:
        """Configure les identifiants utilisateur"""
        # Valide le mot de passe
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        
        # Génère un salt unique
        salt = secrets.token_hex(32)
        
        # Hash du mot de passe avec salt
        password_hash = self._hash_password(password, salt)
        
        # Stocke de manière sécurisée
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        
        self.secret_manager.store_secret("user_credentials", json.dumps(user_data))
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authentifie un utilisateur et retourne un token de session"""
        user_data = self._get_user_data()
        if not user_data:
            return None
        
        # Vérifie le verrouillage de compte
        if self._is_account_locked(user_data):
            raise SecurityError("Account is temporarily locked")
        
        # Vérifie les identifiants
        if (user_data["username"] != username or 
            not self._verify_password(password, user_data["password_hash"], user_data["salt"])):
            self._handle_failed_login(user_data)
            return None
        
        # Réinitialise les tentatives échouées
        user_data["failed_attempts"] = 0
        user_data["last_login"] = datetime.utcnow().isoformat()
        user_data["locked_until"] = None
        self._save_user_data(user_data)
        
        # Crée une session
        return self.session_manager.create_session(username)
    
    def _validate_password_strength(self, password: str) -> bool:
        """Valide la force du mot de passe"""
        if len(password) < 12:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash un mot de passe avec salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # 100k iterations
        ).hex()

class SessionManager:
    """Gestionnaire de sessions utilisateur"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionData] = {}
        self.session_timeout = timedelta(hours=8)
    
    def create_session(self, username: str) -> str:
        """Crée une nouvelle session"""
        session_id = secrets.token_urlsafe(32)
        session_data = SessionData(
            session_id=session_id,
            username=username,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.session_timeout
        )
        
        self.active_sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[SessionData]:
        """Valide une session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        # Vérifie l'expiration
        if datetime.utcnow() > session.expires_at:
            self.revoke_session(session_id)
            return None
        
        # Met à jour l'activité
        session.last_activity = datetime.utcnow()
        return session
    
    def revoke_session(self, session_id: str) -> bool:
        """Révoque une session"""
        return self.active_sessions.pop(session_id, None) is not None
```

## 5. Sécurité des Communications

### Configuration TLS et Validation de Certificats
```python
import ssl
import httpx
from typing import Dict, Any

class SecureHTTPClient:
    """Client HTTP sécurisé pour APIs externes"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self.session_configs = self._create_secure_configs()
    
    def _create_secure_configs(self) -> Dict[str, httpx.AsyncClient]:
        """Crée des configurations sécurisées par service"""
        configs = {}
        
        # Configuration OpenBB
        configs["openbb"] = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            verify=True,  # Vérification SSL stricte
            headers=self._get_security_headers(),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # Configuration OpenRouter/Claude
        configs["openrouter"] = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            verify=True,
            headers=self._get_security_headers(),
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
        )
        
        return configs
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Retourne les headers de sécurité standard"""
        return {
            "User-Agent": "FinAgent/1.0 (Security-Enabled)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "FinAgent",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    async def make_secure_request(
        self,
        service: str,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Effectue une requête sécurisée"""
        client = self.session_configs.get(service)
        if not client:
            raise ValueError(f"No secure client configured for {service}")
        
        # Ajoute la clé API
        api_key = self.api_key_manager.get_api_key(service)
        if not api_key:
            raise SecurityError(f"No API key configured for {service}")
        
        # Configure l'authentification selon le service
        headers = kwargs.get("headers", {})
        if service == "openbb":
            headers["Authorization"] = f"Bearer {api_key}"
        elif service == "openrouter":
            headers["Authorization"] = f"Bearer {api_key}"
        
        kwargs["headers"] = headers
        
        # Log de sécurité (sans exposer les clés)
        security_logger.info(
            "Making secure API request",
            service=service,
            method=method,
            url=self._sanitize_url_for_logging(url)
        )
        
        return await client.request(method, url, **kwargs)
```

## 6. Audit et Logging de Sécurité

### Système d'Audit Sécurisé
```python
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

class SecurityAuditor:
    """Système d'audit pour événements de sécurité"""
    
    def __init__(self, encryption_service: DataEncryption):
        self.encryption = encryption_service
        self.audit_logger = structlog.get_logger("security_audit")
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_level: str = "low"
    ):
        """Log un événement de sécurité"""
        
        event_id = self._generate_event_id()
        timestamp = datetime.utcnow()
        
        audit_event = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "ip_address": self._hash_ip(ip_address) if ip_address else None,
            "user_agent_hash": self._hash_user_agent(user_agent) if user_agent else None,
            "risk_level": risk_level,
            "details": details or {},
            "integrity_hash": None  # Sera calculé après
        }
        
        # Calcule le hash d'intégrité
        audit_event["integrity_hash"] = self._calculate_integrity_hash(audit_event)
        
        # Log selon le niveau de risque
        if risk_level == "critical":
            self.audit_logger.critical("Critical security event", **audit_event)
        elif risk_level == "high":
            self.audit_logger.error("High risk security event", **audit_event)
        elif risk_level == "medium":
            self.audit_logger.warning("Medium risk security event", **audit_event)
        else:
            self.audit_logger.info("Security event", **audit_event)
        
        # Stocke en base pour audit trail persistant
        self._store_audit_event(audit_event)
    
    def _hash_ip(self, ip_address: str) -> str:
        """Hash une adresse IP pour respecter la confidentialité"""
        salt = "finagent_ip_salt_2024"  # Salt fixe pour cohérence
        return hashlib.sha256((ip_address + salt).encode()).hexdigest()[:16]
    
    def _generate_event_id(self) -> str:
        """Génère un ID unique pour l'événement"""
        return secrets.token_urlsafe(16)
    
    def _calculate_integrity_hash(self, event: Dict[str, Any]) -> str:
        """Calcule un hash d'intégrité pour l'événement"""
        # Exclut le hash lui-même du calcul
        event_copy = {k: v for k, v in event.items() if k != "integrity_hash"}
        event_str = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()

# Types d'événements de sécurité
SECURITY_EVENTS = {
    "LOGIN_SUCCESS": "Connexion réussie",
    "LOGIN_FAILED": "Échec de connexion",
    "API_KEY_CREATED": "Clé API créée",
    "API_KEY_USED": "Clé API utilisée",
    "API_KEY_FAILED": "Échec d'authentification API",
    "DATA_EXPORT": "Export de données",
    "CONFIG_CHANGED": "Configuration modifiée",
    "SUSPICIOUS_ACTIVITY": "Activité suspecte détectée",
    "RATE_LIMIT_EXCEEDED": "Limite de taux dépassée",
    "ENCRYPTION_ERROR": "Erreur de chiffrement",
    "INTEGRITY_VIOLATION": "Violation d'intégrité détectée"
}
```

## 7. Protection contre les Attaques

### Protection Multi-Couches
```python
from collections import defaultdict, deque
import time
from typing import Set

class SecurityProtection:
    """Système de protection contre les attaques communes"""
    
    def __init__(self):
        self.rate_limiters = defaultdict(lambda: deque())
        self.suspicious_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 60,
        time_window: int = 60
    ) -> bool:
        """Vérifie les limites de taux"""
        now = time.time()
        requests = self.rate_limiters[identifier]
        
        # Nettoie les anciennes requêtes
        while requests and requests[0] <= now - time_window:
            requests.popleft()
        
        # Vérifie la limite
        if len(requests) >= max_requests:
            self._handle_rate_limit_exceeded(identifier)
            return False
        
        requests.append(now)
        return True
    
    def validate_input(self, input_data: str, input_type: str = "general") -> bool:
        """Valide les entrées utilisateur contre les injections"""
        
        # Patterns suspects généraux
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"eval\(",
            r"exec\(",
            r"import\s+os",
            r"__import__",
            r"\.\.\/",  # Directory traversal
            r"\/etc\/passwd",
            r"cmd\.exe",
            r"powershell",
        ]
        
        # Patterns spécifiques SQL (même si on utilise un ORM)
        if input_type == "database":
            suspicious_patterns.extend([
                r"(union|select|insert|update|delete|drop)\s+",
                r"or\s+1\s*=\s*1",
                r"';?\s*(drop|delete|update)",
            ])
        
        # Vérifie tous les patterns
        for pattern in suspicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                security_auditor.log_security_event(
                    "SUSPICIOUS_INPUT_DETECTED",
                    details={
                        "input_type": input_type,
                        "pattern_matched": pattern,
                        "input_length": len(input_data)
                    },
                    risk_level="high"
                )
                return False
        
        return True
    
    def check_ip_reputation(self, ip_address: str) -> bool:
        """Vérifie la réputation d'une IP"""
        if ip_address in self.blocked_ips:
            return False
        
        if ip_address in self.suspicious_ips:
            # IP suspecte, surveillance renforcée
            return self.check_rate_limit(f"suspicious_ip_{ip_address}", max_requests=10, time_window=60)
        
        return True
    
    def detect_anomalies(self, user_behavior: Dict[str, Any]) -> bool:
        """Détecte les anomalies comportementales"""
        
        # Vérifie les patterns d'accès inhabituels
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            # Accès en dehors des heures normales
            security_auditor.log_security_event(
                "UNUSUAL_ACCESS_TIME",
                details={"access_hour": current_hour},
                risk_level="medium"
            )
        
        # Vérifie la fréquence des requêtes
        request_frequency = user_behavior.get("requests_per_minute", 0)
        if request_frequency > 30:
            security_auditor.log_security_event(
                "HIGH_REQUEST_FREQUENCY",
                details={"requests_per_minute": request_frequency},
                risk_level="high"
            )
            return False
        
        return True

class DataSanitizer:
    """Système de sanitisation des données"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitise un nom de fichier"""
        # Supprime les caractères dangereux
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limite la longueur
        if len(filename) > 255:
            filename = filename[:255]
        
        # Évite les noms réservés
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'LPT1', 'LPT2']
        if filename.upper() in reserved_names:
            filename = f"_{filename}"
        
        return filename
    
    @staticmethod
    def sanitize_symbol(symbol: str) -> str:
        """Sanitise un symbole financier"""
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        # Garde seulement les caractères alphanumériques et quelques symboles autorisés
        allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-')
        sanitized = ''.join(c for c in symbol.upper() if c in allowed_chars)
        
        if len(sanitized) > 10:
            sanitized = sanitized[:10]
        
        if not sanitized:
            raise ValueError("Invalid symbol format")
        
        return sanitized
```

## 8. Conformité et Bonnes Pratiques

### Configuration de Sécurité
```python
class SecurityConfig:
    """Configuration centralisée de sécurité"""
    
    # Politique de mots de passe
    PASSWORD_POLICY = {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digits": True,
        "require_special_chars": True,
        "max_age_days": 90,
        "history_count": 5  # Empêche la réutilisation
    }
    
    # Configuration de session
    SESSION_CONFIG = {
        "timeout_hours": 8,
        "max_concurrent_sessions": 3,
        "require_2fa": False,  # Future feature
        "secure_cookies": True
    }
    
    # Limites de taux
    RATE_LIMITS = {
        "api_calls_per_minute": 60,
        "login_attempts_per_hour": 5,
        "password_reset_per_day": 3,
        "export_operations_per_day": 10
    }
    
    # Configuration de chiffrement
    ENCRYPTION_CONFIG = {
        "algorithm": "AES-256-CBC",
        "key_derivation": "PBKDF2",
        "iterations": 100000,
        "salt_length": 16,
        "iv_length": 16
    }
    
    # Audit et logging
    AUDIT_CONFIG = {
        "log_all_api_calls": True,
        "log_data_access": True,
        "log_config_changes": True,
        "retention_days": 365,
        "encrypt_audit_logs": True
    }

class ComplianceChecker:
    """Vérificateur de conformité sécuritaire"""
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Exécute un audit de sécurité complet"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "score": 0,
            "recommendations": []
        }
        
        # Vérifie la configuration des clés API
        api_check = self._check_api_key_security()
        results["checks"]["api_keys"] = api_check
        
        # Vérifie le chiffrement
        encryption_check = self._check_encryption_config()
        results["checks"]["encryption"] = encryption_check
        
        # Vérifie les permissions de fichiers
        file_permissions_check = self._check_file_permissions()
        results["checks"]["file_permissions"] = file_permissions_check
        
        # Calcule le score global
        total_checks = len(results["checks"])
        passed_checks = sum(1 for check in results["checks"].values() if check["passed"])
        results["score"] = (passed_checks / total_checks) * 100
        
        return results
    
    def _check_api_key_security(self) -> Dict[str, Any]:
        """Vérifie la sécurité des clés API"""
        check_result = {
            "name": "API Key Security",
            "passed": True,
            "details": [],
            "recommendations": []
        }
        
        # Vérifie que les clés sont chiffrées
        try:
            # Tente de lire une clé et vérifie qu'elle n'est pas en plain text
            secret_manager = SecretManager()
            test_key = secret_manager.get_secret("openbb_api_key")
            if test_key and len(test_key) < 20:
                check_result["passed"] = False
                check_result["details"].append("API keys appear to be too short")
        except Exception as e:
            check_result["details"].append(f"Could not verify API key encryption: {e}")
        
        return check_result
```

## 9. Récupération et Continuité

### Plan de Récupération de Sécurité
```python
class SecurityRecoveryManager:
    """Gestionnaire de récupération en cas d'incident de sécurité"""
    
    def __init__(self):
        self.incident_levels = {
            "low": "Incident mineur, surveillance accrue",
            "medium": "Incident modéré, mesures préventives",
            "high": "Incident majeur, restriction d'accès",
            "critical": "Incident critique, arrêt des services"
        }
    
    def handle_security_incident(self, incident_type: str, severity: str):
        """Gère un incident de sécurité"""
        
        if severity == "critical":
            self._emergency_lockdown()
        elif severity == "high":
            self._restrict_operations()
        elif severity == "medium":
            self._enhance_monitoring()
        
        # Log l'incident
        security_auditor.log_security_event(
            "SECURITY_INCIDENT",
            details={
                "incident_type": incident_type,
                "severity": severity,
                "response_taken": self.incident_levels[severity]
            },
            risk_level=severity
        )
    
    def _emergency_lockdown(self):
        """Verrouillage d'urgence du système"""
        # Révoque toutes les sessions actives
        session_manager.revoke_all_sessions()
        
        # Désactive les APIs externes
        api_manager.disable_all_apis()
        
        # Sauvegarde d'urgence
        backup_manager.create_emergency_backup()
        
        logger.critical("Emergency lockdown activated")
    
    def rotate_api_keys(self) -> bool:
        """Effectue une rotation des clés API"""
        try:
            # Backup des anciennes clés
            self._backup_current_keys()
            
            # Génère de nouvelles clés (processus manuel guidé)
            new_keys = self._prompt_for_new_keys()
            
            # Teste les nouvelles clés
            if self._validate_new_keys(new_keys):
                self._update_api_keys(new_keys)
                logger.info("API key rotation completed successfully")
                return True
            else:
                logger.error("New API keys validation failed")
                return False
                
        except Exception as e:
            logger.error(f"API key rotation failed: {e}")
            return False
```

Cette architecture de sécurité offre :
- **Protection multi-couches** : Chiffrement, authentification, autorisation
- **Gestion sécurisée des secrets** : Clés API et données sensibles protégées
- **Audit complet** : Traçabilité de tous les événements de sécurité
- **Détection d'anomalies** : Surveillance comportementale et protection
- **Récupération d'incidents** : Plans de continuité et récupération
- **Conformité** : Respect des bonnes pratiques de sécurité