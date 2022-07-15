# python imports
import uuid
import json
from dataclasses import dataclass, field

# django imports
from django.db import models

# app imports
from lib.django import custom_models
from lib.ddd.exceptions import VOValidationExcpetion

# from lib.data_manipulation.type_conversion import asdict

# local imports


@dataclass(frozen=True)
class FileID:
    """
    This is a value object that should be used to generate and pass the FileID to the FileFactory
    """

    # value: uuid.UUID = field(init=False, default_factory=uuid.uuid4)
    value: uuid.UUID


class File(custom_models.DatedModel):
    """
    A File represents the entrypoint for any type of trades of a given security
    """

    ACTIVE_STATUS = "active"
    DEACTIVATED_STATUS = "deactivated"
    STATUS_CHOICES = [(ACTIVE_STATUS, "Active"), (DEACTIVATED_STATUS, "Deactivated")]

    id = models.UUIDField(primary_key=True, editable=False)
    uploader = models.UUIDField()
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    origin_name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=250, choices=STATUS_CHOICES)
    meta_data = models.JSONField(null=True,blank=True)

    def update_entity(
        self,
        uploader: str,
        title: str,
        description: str,
        origin_name: str,
        location: str,
        status: str,
        meta_data: json
    ):
        if uploader is not None:
            self.uploader = uploader
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if origin_name is not None:
            self.origin_name = origin_name
        if location is not None:
            self.location = location
        if status is not None:
            self.status = status
        if meta_data is not None:
            self.meta_data = meta_data

    class Meta:
        ordering = ["id"]


class FileFactory:
    @staticmethod
    def build_entity(
        file_id: FileID,
        uploader: str,
        title: str,
        description: str,
        origin_name: str,
        location: str,
        status: str,
        meta_data : json,
    ) -> File:
        return File(
            id=file_id.value,
            uploader=uploader,
            title=title,
            description=description,
            origin_name=origin_name,
            location=location,
            status=status,
            meta_data=meta_data
        )

    @classmethod
    def build_entity_with_id(
        cls,
        uploader: str,
        title: str,
        description: str,
        origin_name: str,
        location: str,
        status: str,
        meta_data : json,
    ) -> File:
        file_id = FileID(uuid.uuid4())
        return cls.build_entity(
            file_id, uploader, title, description, origin_name, location, status, meta_data
        )
