from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from kluisz.services.factory import ServiceFactory
from kluisz.services.tracing.service import TracingService

if TYPE_CHECKING:
    from klx.services.settings.service import SettingsService


class TracingServiceFactory(ServiceFactory):
    def __init__(self) -> None:
        super().__init__(TracingService)

    @override
    def create(self, settings_service: SettingsService):
        return TracingService(settings_service)
