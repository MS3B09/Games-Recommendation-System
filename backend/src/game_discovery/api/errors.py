"""Public recovery contracts; private exceptions and prompts never enter messages."""
import logging
import math
from datetime import UTC, datetime
from typing import Literal

from fastapi.responses import JSONResponse
from pydantic import BaseModel

Recovery = Literal['retry', 'edit', 'new_chat', 'refresh', 'discover', 'remove_favorite', 'back', 'none']


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool
    recovery: Recovery = 'retry'
    retry_at: datetime | None = None
    field: Literal['message', 'price', 'request'] | None = None


# message, recovery, retryable, HTTP status
ERRORS: dict[str, tuple[str, Recovery, bool, int]] = {
    'chat_session_missing': ('This chat could not be opened. Start a new chat to continue.', 'new_chat', False, 404),
    'chat_session_conflict': ('This chat changed while you were writing. Refresh to load its latest messages.', 'refresh', False, 409),
    'chat_archive_full': ('Chat storage is full. Your existing messages have been kept. Start a new chat or clear a chat you no longer need.', 'new_chat', False, 503),
    'chat_tool_limit': ("The assistant couldn't finish checking that information within this turn. Please narrow the question.", 'edit', False, 502),
    'chat_daily_calls': ("Today's free chat allowance has been used up. You can still find games using Your taste.", 'discover', True, 429),
    'chat_daily_units': ("Today's free chat allowance has been used up. You can still find games using Your taste.", 'discover', True, 429),
    'chat_rate_limited': ('The assistant needs a short pause before another message. Please wait a moment.', 'retry', True, 429),
    'chat_provider_limited': ('The AI service is receiving too many requests. Please try again later.', 'retry', True, 429),
    'chat_busy': ('The assistant is finishing another reply. Please try again in a moment.', 'retry', True, 503),
    'chat_timeout': ('The assistant took too long to reply. Please try your message again.', 'retry', True, 504),
    'chat_provider_unavailable': ("The assistant can't reach its AI service right now. Please try again later, or find games using Your taste.", 'retry', True, 503),
    'chat_accounting_unavailable': ("We couldn't check whether chat is available right now. Please try again later, or find games using Your taste.", 'retry', True, 503),
    'chat_invalid_answer': ("We couldn't give you a reliable answer to that question. Try asking it another way.", 'edit', False, 502),
    'chat_message_too_long': ('That message is too long. Please keep it under 2,000 characters.', 'edit', False, 422),
    'chat_message_too_detailed': ('That message has more detail than the assistant can handle at once. Please shorten it and try again.', 'edit', False, 422),
    'chat_context_limit': ('This conversation has become too long for the assistant to continue. Start a new chat with your main preferences.', 'new_chat', False, 422),
    'chat_evidence_unavailable': ("The assistant couldn't prepare reliable game details for this request. Try finding games using Your taste.", 'discover', False, 503),
    'chat_unconfigured': ("Chat isn't available on this version of the app. You can still find games using Your taste.", 'discover', False, 503),
    'chat_service_configuration': ("Chat can't connect to its AI service because of a setup issue. You can still find games using Your taste.", 'discover', False, 503),
    'chat_incompatible': ("Chat needs an update before this conversation can continue. Refresh the page. If it still doesn't work, please try again later.", 'refresh', False, 409),
    'database_busy': ('The game catalog is handling other requests. Please try again in a moment.', 'retry', True, 503),
    'database_unavailable': ("We can't load the game catalog right now. Please try again shortly.", 'retry', True, 503),
    'database_unconfigured': ('Game search is unavailable because of a service setup issue. Please try again later.', 'none', False, 503),
    'database_configuration_invalid': ('Game search is unavailable because of a service setup issue. Please try again later.', 'none', False, 503),
    'database_role_misconfigured': ('Game search is unavailable because of a service setup issue. Please try again later.', 'none', False, 503),
    'catalog_not_initialized': ("The game catalog isn't ready yet. Please come back later.", 'none', False, 503),
    'catalog_integrity_error': ("We couldn't load these game details correctly. Please try again later.", 'back', False, 503),
    'unknown_favorite': ('A selected favorite is no longer available in our catalog. Remove unavailable favorites to continue.', 'remove_favorite', False, 422),
    'game_not_found': ('This game is no longer available in our catalog. Choose another game to view its details.', 'back', False, 404),
    'invalid_price_range': ("Choose a maximum price that's at least your minimum price.", 'edit', False, 422),
    'invalid_input': ('Some details in your request need attention. Check your message or filters and try again.', 'edit', False, 422),
    'unexpected_error': ('The service hit an unexpected problem while handling your request. Please try again later.', 'retry', True, 500),
}


def error_response(request_id: str, code: str, *, retry_at: datetime | None = None,
                   field: Literal['message', 'price', 'request'] | None = None) -> JSONResponse:
    if code not in ERRORS:
        code = 'unexpected_error'
    message, recovery, retryable, status = ERRORS[code]
    logging.getLogger('game_discovery.errors').warning('request_failed code=%s request_id=%s', code, request_id)
    headers = {}
    if retry_at is not None:
        headers['Retry-After'] = str(max(0, math.ceil((retry_at - datetime.now(UTC)).total_seconds())))
    error = ApiError(code=code, message=message, recovery=recovery, retryable=retryable,
                     request_id=request_id, retry_at=retry_at, field=field)
    return JSONResponse(status_code=status, content=error.model_dump(mode='json'), headers=headers)


def ai_error_code(code: str) -> str:
    if code in {'chat_session_missing', 'chat_session_conflict', 'chat_archive_full', 'chat_tool_limit'}:
        return code
    mapped = {
        'ai_daily_calls': 'chat_daily_calls', 'ai_daily_units': 'chat_daily_units',
        'ai_minute_limit': 'chat_rate_limited', 'ai_busy': 'chat_busy',
        'ai_provider_limited': 'chat_provider_limited', 'ai_timeout': 'chat_timeout',
        'ai_provider_configuration': 'chat_service_configuration', 'ai_provider_unavailable': 'chat_provider_unavailable',
        'ai_budget_unavailable': 'chat_accounting_unavailable', 'ai_accounting_unavailable': 'chat_accounting_unavailable',
        'chat_required_context_limit': 'chat_message_too_detailed',
        'chat_required_evidence_limit': 'chat_evidence_unavailable',
        'chat_answer_context_limit': 'chat_context_limit',
    }
    invalid = {'ai_output_limit', 'ai_invalid_answer', 'ai_invalid_intent', 'ai_invalid_claims',
               'unsupported_intent', 'chat_invalid_prose', 'chat_candidate_integrity', 'chat_invented_selection'}
    return mapped.get(code, 'chat_invalid_answer' if code in invalid else 'unexpected_error')
