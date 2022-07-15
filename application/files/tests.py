# python imports
from time import sleep
import json
import logging

# django imports
from django.test import TestCase
from django.db.models.query import QuerySet

# app imoprts
from domain.files.models import File
from domain.users.models import UserPersonalData, UserBasePermissions
from application.users.services import UserAppServices
from settings import AWS_STORAGE_BUCKET_NAME, AWS_LOCATION
from application.app_access_control.services import AppAccessControlServices
from infrastructure.logger.models import AttributeLogger
from lib.django.test_helper import set_random_seeds

# local imports
from .services import FileAppServices as fas
from .tests_helper import create_test_file

log = AttributeLogger(logging.getLogger(__name__))

class FileAppServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):

        set_random_seeds()

        cls.u_data_01 = UserPersonalData(
            username="Teser",
            first_name="Testerman",
            last_name="Testerson",
            email="testerman@example.com",
        )
        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=False)
        cls.user_01 = UserAppServices.create_user(cls.u_data_01, cls.u_permissions_01)

        cls.file_app_services = fas(
            AppAccessControlServices(cls.user_01).get_access_controller(), log.with_attributes(user_id=cls.user_01.id)
        )

    def test_list_files(self):
        nqs = self.file_app_services.list_files(self.user_01)
        self.assertEqual(type(nqs), QuerySet)

    def test_create_file(self):
        data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test title",
            "description": "Test description",
            "origin_name": "test.png",
            "location": "https://s3.console.aws.amazon.com/s3/object/dev-general-bucket?region=us-east-2&prefix=test.jpg",
            "status": "active",
            "meta_data" : json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }
        ftc = self.file_app_services.create_file_from_dict(self.user_01, data)
        self.assertEqual(type(ftc), File)

        # Test file was stored
        stored_file = self.file_app_services.file_services.get_file_repo().get(id=ftc.id)
        self.assertEqual(type(stored_file), File)

    def test_update_file(self):
        data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test title",
            "description": "Test description",
            "origin_name": "test.png",
            "location": "https://s3.console.aws.amazon.com/s3/object/dev-general-bucket?region=us-east-2&prefix=test.jpg",
            "status": "active",
            "meta_data" : json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }
        ftc = self.file_app_services.create_file_from_dict(self.user_01, data)

        pre_update_created_at = ftc.created_at
        pre_update_modified_at = ftc.modified_at

        updated_data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test title1",
            "description": "Test description",
            "origin_name": "test.png",
            "location": "https://s3.console.aws.amazon.com/s3/object/dev-general-bucket?region=us-east-2&prefix=test.jpg",
            "status": "active",
            "meta_data" : json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }

        sleep(0.000001)
        self.file_app_services.update_file_from_dict(self.user_01, ftc, updated_data)

        ftc.refresh_from_db()
        self.assertEqual(ftc.title, "Test title1")

        self.assertEqual(ftc.created_at, pre_update_created_at)
        self.assertNotEqual(ftc.modified_at, pre_update_modified_at)

    def test_file_delete_soft(self):
        data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test title",
            "description": "Test description",
            "origin_name": "test.png",
            "location": "https://s3.console.aws.amazon.com/s3/object/dev-general-bucket?region=us-east-2&prefix=test.jpg",
            "status": "active",
            "meta_data" : json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }
        ftc = self.file_app_services.create_file_from_dict(self.user_01, data)
        self.assertEqual(type(ftc), File)

        # Test file was stored
        stored_file = self.file_app_services.file_services.get_file_repo().get(id=ftc.id)
        self.assertEqual(type(stored_file), File)

        # Test file soft delete
        updated_file = self.file_app_services.delete_file_soft(ftc.id)
        self.assertEqual(updated_file.status, "deactivated")

    def test_upload_file_to_s3(self):
        # creating testing file
        test_file = create_test_file()

        # uploading file to s3 bucket
        test_url = self.file_app_services.file_upload_s3(self.user_01, test_file)

        # testing uploading status
        self.assertEqual(type(test_url), str)

        # testing deleting file
        self.assertEqual(
            self.file_app_services.file_delete_s3(self.user_01, test_url), True
        )
