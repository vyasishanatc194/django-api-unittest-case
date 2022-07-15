#python imports
import json
import logging

# django imports
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import force_authenticate, APIRequestFactory
from rest_framework.test import APITestCase

# app imports
from domain.users.models import UserPersonalData, UserBasePermissions
from application.users.services import UserAppServices
from application.files.services import FileAppServices as fas
from application.files.tests_helper import create_test_file
from application.app_access_control.services import AppAccessControlServices
from infrastructure.logger.models import AttributeLogger

# local imports
from . import views

from settings import BASE_DIR

log = AttributeLogger(logging.getLogger(__name__))

RESOURCE_ACTIONS = {
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
}

COLLECTION_ACTIONS = {
    "get": "list",
}


class FileViewSetTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.file_resource_view = views.FileViewSet.as_view(RESOURCE_ACTIONS)
        cls.file_collection_view = views.FileViewSet.as_view(COLLECTION_ACTIONS)
        cls.file_upload_view = views.FileUploadViewSet.as_view({"post": "create"})
        cls.file_download_view = views.FileDownloadViewSet.as_view({"post": "create"})
        cls.file_serve_view = views.FileViewSet.as_view({"get": "serve"})

        cls.u_data_01 = UserPersonalData(
            username="Teser",
            first_name="Testerman",
            last_name="Testerson",
            email="testerman@example.com",
        )
        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=False)
        cls.user_01 = UserAppServices.create_user(cls.u_data_01, cls.u_permissions_01)

        # Create a test file  "c13cce88-42e3-40a1-9402-abf7e2f0a297", "Test Title", "Test Description", "https://dev-general-bucket.s3.amazonaws.com/media/Teser/test.png"
        data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test Title",
            "description": "Test Description",
            "origin_name": "test.png",
            "location": "https://dev-general-bucket.s3.amazonaws.com/media/Teser/test.png",
            "status": "active",
            "meta_data":json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }

        cls.file_app_services = fas(
            AppAccessControlServices(cls.user_01).get_access_controller(),
            log.with_attributes(user_id=cls.user_01.id)
        )
        cls.fkt = cls.file_app_services.create_file_from_dict(cls.user_01, data)


    def test_file_upload(self):
        # creating testing file
        test_file = create_test_file(fmt='json')
        uploaded_file = SimpleUploadedFile('test_file_01.json', test_file.read(), content_type='application/json')
        upload_params = {
            'upload_file': uploaded_file,
            'file_type': '',
            'size_soft_limit_mb': '',
        }

        # test upload and creating file
        request = self.factory.post('/api/v0/file/upload/', upload_params, format='multipart')
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

    def test_file_upload(self):
        # creating testing file
        test_file = create_test_file(fmt="json")
        uploaded_file = SimpleUploadedFile(
            "test_file_01.json", test_file.read(), content_type="application/json"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "",
            "size_soft_limit_mb": "",
        }

        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

    def test_file_upload_file_type(self):
        # creating testing file
        test_file = create_test_file(fmt="json")
        # test upload and creating file
        request = self.factory.post("/api/v0/file/upload/", {"upload_file": test_file})

        uploaded_file = SimpleUploadedFile(
            "test_file_01.json", test_file.read(), content_type="application/json"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "application/json",
            "size_soft_limit_mb": "",
        }
        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

    def test_file_upload_size_soft_limit_mb(self):
        # creating testing file
        test_file = create_test_file(fmt="json")
        uploaded_file = SimpleUploadedFile(
            "test_file_01.json", test_file.read(), content_type="application/json"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "",
            "size_soft_limit_mb": "5",
        }

        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

    def test_file_upload_download(self):
        # creating testing file
        test_file = create_test_file(fmt="json")
        # file = b'super_user\r\nBBVA\r\nScotiabank\r\nActinver\r\nBanamex\r\nHSBC\r\nSantander'
        uploaded_file = SimpleUploadedFile(
            "test_file.json", test_file.read(), content_type="application/json"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "",
            "size_soft_limit_mb": "",
        }

        # data = {'upload_file': test_file}

        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

        file_id = response.data["file_id"]
        upload_key = response.data["upload_key"]

        # test download file
        request = self.factory.post("/api/v0/file/download/", {"file_id": file_id})
        force_authenticate(request, user=self.user_01)
        response = self.file_download_view(request)
        self.assertIs(response.status_code, 200)

        # test deleting object from s3 using key
        self.assertEqual(
            self.file_app_services.file_delete_s3(request.user, upload_key), True
        )

    def test_file_upload_serve(self):
        # creating testing file
        test_file = create_test_file(fmt="json")
        # file = b'super_user\r\nBBVA\r\nScotiabank\r\nActinver\r\nBanamex\r\nHSBC\r\nSantander'
        uploaded_file = SimpleUploadedFile(
            "test_file.json", test_file.read(), content_type="application/json"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "",
            "size_soft_limit_mb": "",
        }

        # data = {'upload_file': test_file}

        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)

        file_id = response.data["file_id"]
        upload_key = response.data["upload_key"]

        # test download file
        request = self.factory.get("/api/v0/{}/serve/".format(file_id))
        force_authenticate(request, user=self.user_01)
        response = self.file_serve_view(request, pk=file_id)
        self.assertIs(response.status_code, 200)

        # test deleting object from s3 using key
        self.assertEqual(
            self.file_app_services.file_delete_s3(request.user, upload_key), True
        )

    def test_update_files(self):
        data = {
            "uploader": "c13cce88-42e3-40a1-9402-abf7e2f0a297",
            "title": "Test Title1",
            "description": "Test Description",
            "origin_name": "test.png",
            "location": "https://dev-general-bucket.s3.amazonaws.com/media/Teser/test.png",
            "status": "active",
            "meta_data":json.dumps({'height':100,'width':100,'mime_type':'image/png','filesize_in_bytes':2000})
        }
        request = self.factory.put("/api/v0/file/{}".format(self.fkt.id), data)
        force_authenticate(request, user=self.user_01)
        response = self.file_resource_view(request, pk=self.fkt.id)

        self.assertIs(response.status_code, 200)

    def test_list_files(self):
        request = self.factory.get("/api/v0/file/")
        force_authenticate(request, user=self.user_01)
        response = self.file_collection_view(request)

        self.assertIs(response.status_code, 200)

    def test_retrieve_file_dummy_data(self):
        request = self.factory.get("/api/v0/file/{}".format(self.fkt.id))
        force_authenticate(request, user=self.user_01)

        response = self.file_resource_view(request, pk=self.fkt.id)

        self.assertIs(response.status_code, 200)

    def test_image_upload_size_validation(self):
        # creating testing file
        test_file = create_test_file(fmt="png")
        uploaded_file = SimpleUploadedFile(
            "test_file_01.png", test_file.read(), content_type="image/png"
        )
        upload_params = {
            "upload_file": uploaded_file,
            "file_type": "",
            "size_soft_limit_mb": "5",
        }

        # test upload and creating file
        request = self.factory.post(
            "/api/v0/file/upload/", upload_params, format="multipart"
        )
        force_authenticate(request, user=self.user_01)
        response = self.file_upload_view(request)
        self.assertIs(response.status_code, 200)