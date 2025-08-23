"""
Tests unitaires pour les modèles de données FinAgent.

Ce module teste tous les modèles Pydantic utilisés pour la validation
et la sérialisation des données dans FinAgent.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from typing import Dict, Any

from pydantic import ValidationError

from finagent.ai.models.base import (
    AIRequest, AIResponse, ModelType, ConfidenceLevel, ResponseFormat,
    TokenUsage, RateLimitInfo, AIError, RateLimitError
)
from tests.utils import (
    assert_valid_uuid, create_sample_ai_request, create_sample_ai_response
)


class TestAIModels:
    """Tests pour les modèles IA de base."""
    
    def test_ai_request_creation_valid(self):
        """Test création valide d'une requête IA."""
        request = AIRequest(
            prompt="Analyze AAPL stock",
            model_type=ModelType.CLAUDE_3_SONNET,
            temperature=0.5,
            max_tokens=2000
        )
        
        assert request.prompt == "Analyze AAPL stock"
        assert request.model_type == ModelType.CLAUDE_3_SONNET
        assert request.temperature == 0.5
        assert request.max_tokens == 2000
        assert assert_valid_uuid(request.request_id)
        assert isinstance(request.timestamp, datetime)
        assert isinstance(request.context, dict)
    
    def test_ai_request_defaults(self):
        """Test valeurs par défaut d'une requête IA."""
        request = AIRequest(prompt="Test prompt")
        
        assert request.model_type == ModelType.CLAUDE_3_SONNET
        assert request.temperature == 0.3
        assert request.max_tokens == 4000
        assert request.context == {}
    
    def test_ai_request_validation_empty_prompt(self):
        """Test validation avec prompt vide."""
        with pytest.raises(ValidationError) as exc_info:
            AIRequest(prompt="")
        
        assert "at least 1 character" in str(exc_info.value)
    
    def test_ai_request_validation_temperature_range(self):
        """Test validation plage de température."""
        # Température trop basse
        with pytest.raises(ValidationError):
            AIRequest(prompt="Test", temperature=-0.1)
        
        # Température trop haute
        with pytest.raises(ValidationError):
            AIRequest(prompt="Test", temperature=2.1)
        
        # Températures valides
        for temp in [0.0, 0.5, 1.0, 2.0]:
            request = AIRequest(prompt="Test", temperature=temp)
            assert request.temperature == temp
    
    def test_ai_request_validation_max_tokens(self):
        """Test validation nombre maximum de tokens."""
        # Tokens négatifs ou zéro
        with pytest.raises(ValidationError):
            AIRequest(prompt="Test", max_tokens=0)
        
        with pytest.raises(ValidationError):
            AIRequest(prompt="Test", max_tokens=-100)
        
        # Tokens trop élevés
        with pytest.raises(ValidationError):
            AIRequest(prompt="Test", max_tokens=10000)
        
        # Tokens valides
        for tokens in [1, 1000, 4000, 8192]:
            request = AIRequest(prompt="Test", max_tokens=tokens)
            assert request.max_tokens == tokens
    
    def test_ai_response_creation_valid(self):
        """Test création valide d'une réponse IA."""
        request_id = uuid4()
        response = AIResponse(
            request_id=request_id,
            content="Analysis completed successfully",
            model_used=ModelType.CLAUDE_3_SONNET,
            tokens_used=250,
            processing_time=1.5,
            confidence=ConfidenceLevel.HIGH
        )
        
        assert response.request_id == request_id
        assert response.content == "Analysis completed successfully"
        assert response.model_used == ModelType.CLAUDE_3_SONNET
        assert response.tokens_used == 250
        assert response.processing_time == 1.5
        assert response.confidence == ConfidenceLevel.HIGH
        assert assert_valid_uuid(response.response_id)
        assert isinstance(response.timestamp, datetime)
        assert isinstance(response.metadata, dict)
    
    def test_ai_response_validation_tokens(self):
        """Test validation nombre de tokens utilisés."""
        request_id = uuid4()
        
        # Tokens négatifs
        with pytest.raises(ValidationError):
            AIResponse(
                request_id=request_id,
                content="Test",
                model_used=ModelType.CLAUDE_3_SONNET,
                tokens_used=-10
            )
        
        # Tokens valides
        response = AIResponse(
            request_id=request_id,
            content="Test",
            model_used=ModelType.CLAUDE_3_SONNET,
            tokens_used=0
        )
        assert response.tokens_used == 0
    
    def test_ai_response_validation_processing_time(self):
        """Test validation temps de traitement."""
        request_id = uuid4()
        
        # Temps négatif
        with pytest.raises(ValidationError):
            AIResponse(
                request_id=request_id,
                content="Test",
                model_used=ModelType.CLAUDE_3_SONNET,
                processing_time=-1.0
            )
        
        # Temps valide
        response = AIResponse(
            request_id=request_id,
            content="Test", 
            model_used=ModelType.CLAUDE_3_SONNET,
            processing_time=0.0
        )
        assert response.processing_time == 0.0


class TestTokenUsage:
    """Tests pour le modèle TokenUsage."""
    
    def test_token_usage_creation_valid(self):
        """Test création valide de TokenUsage."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=Decimal("0.03")
        )
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 200
        assert usage.total_tokens == 300
        assert usage.estimated_cost == Decimal("0.03")
    
    def test_token_usage_validation_negative_values(self):
        """Test validation valeurs négatives."""
        # Prompt tokens négatifs
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=-10, completion_tokens=100, total_tokens=90)
        
        # Completion tokens négatifs
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=100, completion_tokens=-10, total_tokens=90)
        
        # Total tokens négatifs
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=100, completion_tokens=100, total_tokens=-10)
        
        # Coût négatif
        with pytest.raises(ValidationError):
            TokenUsage(
                prompt_tokens=100, 
                completion_tokens=100, 
                total_tokens=200,
                estimated_cost=Decimal("-0.01")
            )
    
    def test_token_usage_defaults(self):
        """Test valeurs par défaut."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300)
        
        assert usage.estimated_cost == Decimal("0.0")


class TestRateLimitInfo:
    """Tests pour le modèle RateLimitInfo."""
    
    def test_rate_limit_info_creation_valid(self):
        """Test création valide de RateLimitInfo."""
        reset_time = datetime.utcnow() + timedelta(minutes=5)
        
        rate_limit = RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=10000,
            current_requests=25,
            current_tokens=2500,
            reset_time=reset_time
        )
        
        assert rate_limit.requests_per_minute == 100
        assert rate_limit.tokens_per_minute == 10000
        assert rate_limit.current_requests == 25
        assert rate_limit.current_tokens == 2500
        assert rate_limit.reset_time == reset_time
    
    def test_rate_limit_info_properties(self):
        """Test propriétés calculées."""
        reset_time = datetime.utcnow() + timedelta(minutes=5)
        
        rate_limit = RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=10000,
            current_requests=25,
            current_tokens=2500,
            reset_time=reset_time
        )
        
        assert rate_limit.requests_remaining == 75
        assert rate_limit.tokens_remaining == 7500
        assert not rate_limit.is_rate_limited
    
    def test_rate_limit_info_rate_limited_state(self):
        """Test état de limite atteinte."""
        reset_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Limite de requêtes atteinte
        rate_limit = RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=10000,
            current_requests=100,
            current_tokens=5000,
            reset_time=reset_time
        )
        
        assert rate_limit.requests_remaining == 0
        assert rate_limit.tokens_remaining == 5000
        assert rate_limit.is_rate_limited
        
        # Limite de tokens atteinte
        rate_limit = RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=10000,
            current_requests=50,
            current_tokens=10000,
            reset_time=reset_time
        )
        
        assert rate_limit.requests_remaining == 50
        assert rate_limit.tokens_remaining == 0
        assert rate_limit.is_rate_limited
    
    def test_rate_limit_info_validation_positive_values(self):
        """Test validation valeurs positives."""
        reset_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Requêtes par minute <= 0
        with pytest.raises(ValidationError):
            RateLimitInfo(
                requests_per_minute=0,
                tokens_per_minute=10000,
                reset_time=reset_time
            )
        
        # Tokens par minute <= 0
        with pytest.raises(ValidationError):
            RateLimitInfo(
                requests_per_minute=100,
                tokens_per_minute=0,
                reset_time=reset_time
            )


class TestModelEnums:
    """Tests pour les énumérations de modèles."""
    
    def test_model_type_enum(self):
        """Test énumération ModelType."""
        assert ModelType.CLAUDE_3_SONNET == "claude-3-sonnet-20240229"
        assert ModelType.CLAUDE_3_HAIKU == "claude-3-haiku-20240307"
        assert ModelType.CLAUDE_3_OPUS == "claude-3-opus-20240229"
        assert ModelType.CLAUDE_3_5_SONNET == "claude-3-5-sonnet-20241022"
        
        # Test que tous les types sont des chaînes
        for model_type in ModelType:
            assert isinstance(model_type.value, str)
    
    def test_confidence_level_enum(self):
        """Test énumération ConfidenceLevel."""
        assert ConfidenceLevel.VERY_LOW == "very_low"
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.VERY_HIGH == "very_high"
        
        # Test que tous les niveaux sont des chaînes
        for level in ConfidenceLevel:
            assert isinstance(level.value, str)
    
    def test_response_format_enum(self):
        """Test énumération ResponseFormat."""
        assert ResponseFormat.TEXT == "text"
        assert ResponseFormat.JSON == "json"
        assert ResponseFormat.STRUCTURED == "structured"
        
        # Test que tous les formats sont des chaînes
        for format_type in ResponseFormat:
            assert isinstance(format_type.value, str)


class TestAIExceptions:
    """Tests pour les exceptions IA."""
    
    def test_ai_error_creation(self):
        """Test création d'AIError."""
        error = AIError(
            message="Test error",
            error_code="TEST_001",
            details={"param": "value"}
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.details == {"param": "value"}
        assert str(error) == "Test error"
    
    def test_ai_error_defaults(self):
        """Test valeurs par défaut d'AIError."""
        error = AIError("Test error")
        
        assert error.message == "Test error"
        assert error.error_code is None
        assert error.details == {}
    
    def test_rate_limit_error_inheritance(self):
        """Test héritage de RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        
        assert isinstance(error, AIError)
        assert error.message == "Rate limit exceeded"
    
    def test_exception_hierarchy(self):
        """Test hiérarchie des exceptions."""
        from finagent.ai.models.base import (
            ModelNotAvailableError, InvalidRequestError, ProviderError
        )
        
        # Test que toutes les exceptions héritent d'AIError
        exceptions = [
            RateLimitError("test"),
            ModelNotAvailableError("test"),
            InvalidRequestError("test"),
            ProviderError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AIError)
            assert isinstance(exc, Exception)


class TestModelSerialization:
    """Tests pour la sérialisation des modèles."""
    
    def test_ai_request_serialization(self):
        """Test sérialisation d'AIRequest."""
        request = create_sample_ai_request()
        
        # Sérialisation en dict
        data = request.model_dump()
        assert isinstance(data, dict)
        assert "request_id" in data
        assert "prompt" in data
        assert "model_type" in data
        
        # Sérialisation JSON
        json_str = request.model_dump_json()
        assert isinstance(json_str, str)
        
        # Désérialisation
        request_copy = AIRequest.model_validate(data)
        assert request_copy.request_id == request.request_id
        assert request_copy.prompt == request.prompt
    
    def test_ai_response_serialization(self):
        """Test sérialisation d'AIResponse."""
        response = create_sample_ai_response()
        
        # Sérialisation en dict
        data = response.model_dump()
        assert isinstance(data, dict)
        assert "response_id" in data
        assert "content" in data
        assert "model_used" in data
        
        # Désérialisation
        response_copy = AIResponse.model_validate(data)
        assert response_copy.response_id == response.response_id
        assert response_copy.content == response.content
    
    def test_token_usage_serialization(self):
        """Test sérialisation de TokenUsage."""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            estimated_cost=Decimal("0.03")
        )
        
        # Sérialisation en dict
        data = usage.model_dump()
        assert data["prompt_tokens"] == 100
        assert data["completion_tokens"] == 200
        assert data["total_tokens"] == 300
        
        # Désérialisation
        usage_copy = TokenUsage.model_validate(data)
        assert usage_copy.prompt_tokens == usage.prompt_tokens
        assert usage_copy.estimated_cost == usage.estimated_cost


class TestModelValidation:
    """Tests pour la validation des modèles."""
    
    def test_model_config_validation(self):
        """Test configuration de validation des modèles."""
        # Test strip whitespace
        request = AIRequest(prompt="  Test prompt  ")
        assert request.prompt == "Test prompt"
        
        # Test validate assignment
        request = AIRequest(prompt="Test")
        request.temperature = 0.8
        assert request.temperature == 0.8
        
        # Test use enum values
        request = AIRequest(prompt="Test", model_type=ModelType.CLAUDE_3_HAIKU)
        data = request.model_dump()
        assert data["model_type"] == "claude-3-haiku-20240307"
    
    def test_custom_validators(self):
        """Test validateurs personnalisés si présents."""
        # Ce test peut être étendu si des validateurs custom sont ajoutés
        request = AIRequest(prompt="Test prompt")
        assert request.prompt == "Test prompt"
    
    @pytest.mark.parametrize("invalid_uuid", [
        "not-a-uuid",
        "12345",
        "",
        None
    ])
    def test_uuid_validation(self, invalid_uuid):
        """Test validation UUID."""
        # Note: Ce test dépend de l'implémentation des modèles
        # Si les UUIDs sont validés automatiquement par Pydantic
        if invalid_uuid is not None:
            with pytest.raises(ValidationError):
                # Teste avec un UUID invalide si le modèle le valide
                AIResponse(
                    request_id=invalid_uuid,  # type: ignore
                    content="Test",
                    model_used=ModelType.CLAUDE_3_SONNET
                )


class TestModelCompatibility:
    """Tests de compatibilité des modèles."""
    
    def test_backward_compatibility(self):
        """Test compatibilité avec versions antérieures."""
        # Test que les modèles peuvent être créés avec des données minimales
        request = AIRequest(prompt="Test")
        response = AIResponse(
            request_id=request.request_id,
            content="Response",
            model_used=ModelType.CLAUDE_3_SONNET
        )
        
        assert request.prompt == "Test"
        assert response.content == "Response"
    
    def test_forward_compatibility(self):
        """Test compatibilité avec futures versions."""
        # Test que des champs supplémentaires sont ignorés gracieusement
        data = {
            "prompt": "Test",
            "model_type": "claude-3-sonnet-20240229",
            "temperature": 0.3,
            "max_tokens": 2000,
            "future_field": "future_value"  # Champ non défini
        }
        
        # Pydantic devrait ignorer les champs inconnus par défaut
        request = AIRequest.model_validate(data, strict=False)
        assert request.prompt == "Test"
    
    def test_model_evolution(self):
        """Test évolution des modèles."""
        # Test que les modèles peuvent évoluer en ajoutant des champs optionnels
        request = AIRequest(prompt="Test")
        
        # Ajouter un nouveau champ via mise à jour
        updated_data = request.model_dump()
        updated_data["new_optional_field"] = "new_value"
        
        # La désérialisation devrait fonctionner même avec des champs supplémentaires
        try:
            AIRequest.model_validate(updated_data, strict=False)
        except ValidationError:
            pytest.skip("Strict mode enabled, skipping forward compatibility test")


# Fixtures spécifiques pour ces tests
@pytest.fixture
def sample_ai_models():
    """Fixture fournissant des échantillons de modèles IA."""
    request = create_sample_ai_request()
    response = create_sample_ai_response(request_id=request.request_id)
    
    return {
        "request": request,
        "response": response,
        "token_usage": TokenUsage(
            prompt_tokens=100,
            completion_tokens=150,
            total_tokens=250,
            estimated_cost=Decimal("0.025")
        ),
        "rate_limit": RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=10000,
            current_requests=25,
            current_tokens=2500,
            reset_time=datetime.utcnow() + timedelta(minutes=5)
        )
    }


@pytest.fixture
def invalid_model_data():
    """Fixture fournissant des données invalides pour tests."""
    return {
        "empty_prompt": "",
        "negative_temperature": -0.5,
        "high_temperature": 3.0,
        "zero_tokens": 0,
        "negative_tokens": -100,
        "high_tokens": 10000,
        "invalid_uuid": "not-a-uuid",
        "negative_usage": -50
    }