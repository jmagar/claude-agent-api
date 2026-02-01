# Session Log: Fix test failures

16:11:09 | 01/31/2026

## Summary
- Resolved permission_mode defaults to use "default" for QueryRequest and OpenAI translation.
- Enabled gpt-4 validation for request schemas and OpenAI mapping without changing core ModelMapper behavior.
- Updated OpenAI response formatting and streaming model emission to satisfy compatibility tests.
- Adjusted cache creation tests to account for retry configuration.
- Updated schema tests to use invalid model placeholders now that gpt-4 is accepted.

## Changes
- apps/api/schemas/requests/query.py
- apps/api/services/openai/translator.py
- apps/api/types.py
- apps/api/routes/openai/dependencies.py
- apps/api/routes/openai/chat.py
- tests/unit/adapters/test_cache.py
- tests/unit/test_validators.py
- tests/unit/test_request_query_schema.py
- tests/unit/test_request_sessions_schema.py
- tests/unit/test_schemas.py
- tests/integration/test_openai_chat.py
- tests/unit/test_error_handlers.py

## Tests
- `uv run pytest`
