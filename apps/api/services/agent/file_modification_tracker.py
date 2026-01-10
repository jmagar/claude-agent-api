"""<summary>Track file modifications from content blocks.</summary>"""

from typing import TYPE_CHECKING

from apps.api.schemas.responses import ContentBlockSchema
from apps.api.services.agent.types import StreamContext

if TYPE_CHECKING:
    from apps.api.services.agent.handlers import MessageHandler


class FileModificationTracker:
    """<summary>Converts blocks and forwards to MessageHandler.</summary>"""

    def __init__(self, message_handler: "MessageHandler") -> None:
        """<summary>Initialize with a message handler.</summary>"""
        self._message_handler = message_handler

    def track(self, content_blocks: list[object], ctx: StreamContext) -> None:
        """<summary>Convert blocks and forward tracking.</summary>"""
        typed_blocks: list[ContentBlockSchema] = []
        for block in content_blocks:
            if isinstance(block, ContentBlockSchema):
                typed_blocks.append(block)
            elif isinstance(block, dict):
                typed_blocks.append(ContentBlockSchema(**block))

        self._message_handler.track_file_modifications(typed_blocks, ctx)
