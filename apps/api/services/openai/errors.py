"""OpenAI error translation service."""

from apps.api.exceptions.base import APIError
from apps.api.schemas.openai.responses import OpenAIError


class ErrorTranslator:
    """Translates API errors to OpenAI-compatible error format."""

    @staticmethod
    def translate(error: APIError) -> OpenAIError:
        """Translate APIError to OpenAI error format.

        Maps HTTP status codes to OpenAI error types:
        - 401 → authentication_error
        - 400 → invalid_request_error
        - 429 → rate_limit_exceeded
        - 500+ → api_error

        Args:
            error: APIError instance with status_code, message, and code.

        Returns:
            OpenAI-compatible error dictionary with type, message, and code.
        """
        # Map status code to OpenAI error type
        error_type = ErrorTranslator._map_status_to_type(error.status_code)

        return {
            "error": {
                "type": error_type,
                "message": error.message,
                "code": error.code,
            }
        }

    @staticmethod
    def _map_status_to_type(status_code: int) -> str:
        """Map HTTP status code to OpenAI error type.

        Args:
            status_code: HTTP status code from APIError.

        Returns:
            OpenAI error type string.
        """
        # Map status codes to OpenAI error types
        status_map = {
            401: "authentication_error",
            400: "invalid_request_error",
            429: "rate_limit_exceeded",
        }
        # Default to api_error for 5xx and other status codes
        return status_map.get(status_code, "api_error")
