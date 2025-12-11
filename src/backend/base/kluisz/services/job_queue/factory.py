from kluisz.services.base import Service
from kluisz.services.factory import ServiceFactory
from kluisz.services.job_queue.service import JobQueueService


class JobQueueServiceFactory(ServiceFactory):
    def __init__(self):
        super().__init__(JobQueueService)

    def create(self) -> Service:
        return JobQueueService()
