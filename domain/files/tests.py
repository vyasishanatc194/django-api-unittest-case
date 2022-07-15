# python imports
import json
import logging

# django imports
from django.test import TestCase
from django.db.models.manager import Manager

# app imports
from lib.ddd.exceptions import VOValidationExcpetion
from domain.users.models import UserPersonalData, UserBasePermissions
from application.users.services import UserAppServices
from infrastructure.logger.models import AttributeLogger

# local imports
from .models import File, FileID, FileFactory
from .services import FileServices
from . import tests_helper as th

log = AttributeLogger(logging.getLogger(__name__))

class FileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u_data_01 = UserPersonalData(
            username="Teser",
            first_name="Testerman",
            last_name="Testerson",
            email="testerman@example.com",
        )
        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=False)
        cls.user_01 = UserAppServices.create_user(cls.u_data_01, cls.u_permissions_01)
        cls.file_services = FileServices(log.with_attributes(user_id=cls.user_01.id))

    def test_build_file_id(self):
        try:
            m = FileID
        except Exception:
            self.fail("Unexpected exception")

    def test_build_file(self):
        try:
            self.file_services.get_file_factory().build_entity_with_id(
                "c13cce88-42e3-40a1-9402-abf7e2f0a297",
                "Test Title",
                "Test Descriptoin",
                "test.png",
                "https://dev-general-bucket.s3.amazonaws.com/media/Teser/test.png",
                "active",
                json.dumps(
                    {
                        "height": 100,
                        "width": 100,
                        "mime_type": "image/png",
                        "filesize_in_bytes": 2000,
                    }
                ),
            )
        except Exception:
            self.fail("Unexpected exception")

    def test_build_files(self):
        mkts = th.generate_random_files(self.user_01, 5)
        self.assertEquals(len(mkts), 5)


class FileServicesTests(TestCase):
    def test_get_file_repo(self):
        repo = FileServices(log).get_file_repo()
        self.assertEquals(Manager, type(repo))
