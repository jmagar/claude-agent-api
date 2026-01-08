"""Validation-related exceptions."""

from apps.api.exceptions.base import APIError


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Validation error message.
            field: Optional field that failed validation.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class StructuredOutputValidationError(APIError):
    """Raised when structured output validation fails.

    This error is raised when the agent's output does not conform to
    the JSON schema specified in output_format.
    """

    def __init__(
        self,
        message: str = "Structured output validation failed",
        validation_errors: list[str] | None = None,
        schema_type: str | None = None,
    ) -> None:
        """Initialize structured output validation error.

        Args:
            message: Error message.
            validation_errors: List of specific validation error messages.
            schema_type: The output format type that was requested.
        """
        details: dict[str, str | int | float | bool | list[str] | None] = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if schema_type:
            details["schema_type"] = schema_type
        super().__init__(
            message=message,
            code="STRUCTURED_OUTPUT_VALIDATION_ERROR",
            status_code=422,
            details=details,
        )
