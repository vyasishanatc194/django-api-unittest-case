# python imports
from typing import Type

# django imports
from django.db.models.manager import Manager

# app imports
from infrastructure.logger.models import AttributeLogger

# local imports
from .models import FileFactory
from .models import File


class FileServices:
    def __init__(self, log: AttributeLogger):
        self.log = log

    def get_file_factory(self) -> Type[FileFactory]:
        return FileFactory

    def get_file_repo(self) -> Type[Manager]:
        # We expose the whole repository as a service to avoid making a service for each repo action. If some repo action is used constantly in multiple places consider exposing it as a service.
        return File.objects
