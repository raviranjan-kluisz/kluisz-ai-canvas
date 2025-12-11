from fastapi_pagination import Page

from kluisz.helpers.base_model import BaseModel
from kluisz.services.database.models.flow.model import Flow
from kluisz.services.database.models.folder.model import FolderRead


class FolderWithPaginatedFlows(BaseModel):
    folder: FolderRead
    flows: Page[Flow]


# Rebuild model to ensure all types are resolved
FolderWithPaginatedFlows.model_rebuild()
