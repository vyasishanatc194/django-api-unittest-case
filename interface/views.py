# python imports
import logging

# django imports
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view
from rest_framework.parsers import MultiPartParser
from django.utils.decorators import decorator_from_middleware_with_args

# app imports
from lib.django.custom_views import ListUpdateRetrieveViewSet
from application.files.services import FileAppServices as fas
from interface.access_control.middleware import UacMiddlewareWithLogger
from infrastructure.logger.models import AttributeLogger

# TODO: improve error handling

# local imports
from . import open_api
from .serializers import FileSerializer
from .serializer_upload import UploadSerializer
from .serializer_download import DownloadSerializer

logger = AttributeLogger(logging.getLogger(__name__))


@extend_schema_view(
    list=open_api.file_list_extension, serve=open_api.file_serve_extension
)
class FileViewSet(ListUpdateRetrieveViewSet):
    """
    Allows clients to perform retrieve and list Files
    """

    serializer_class = FileSerializer
    ordering = ["-created_at"]

    access_control = decorator_from_middleware_with_args(UacMiddlewareWithLogger)

    @access_control()
    def get_queryset(self):
        file_app_services = fas(self.user_access_controller, self.log)
        return file_app_services.list_files(self.request.user)

    @access_control()
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "user_access_controller": self.user_access_controller,
                "log": self.log
            }
        )
        return context

    @access_control()
    @action(detail=True, methods=["get"], name="serve")
    def serve(self, request, pk=None):
        file_app_services = fas(self.user_access_controller, self.log)
        # get id of file from request
        fobj = file_app_services.get_file(request.user, pk)
        response = file_app_services.file_download_from_s3(
            request.user, fobj.location, fobj.origin_name
        )
        return response


class FileUploadViewSet(ViewSet):
    serializer_class = UploadSerializer
    parser_classes = (MultiPartParser,)

    access_control = decorator_from_middleware_with_args(UacMiddlewareWithLogger)

    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    @access_control()
    def create(self, request):
        file_app_services = fas(self.user_access_controller, self.log)

        # get file from request
        data = {
            "upload_file":request.FILES.get("upload_file"),
            "size_soft_limit_mb": request.data.get("size_soft_limit_mb"),
            "file_type":request.data.get("file_type")
        }

        upload_key, fobj = file_app_services.upload_file(data)
        
        response_data = {"upload_key": upload_key, "file_id": fobj.id}
        logger.debug(
            "File created - upload_key {} and file_id {}".format(upload_key, fobj.id)
        )

        return Response(response_data)


class FileDownloadViewSet(ViewSet):
    serializer_class = DownloadSerializer

    access_control = decorator_from_middleware_with_args(UacMiddlewareWithLogger)

    @access_control()
    def create(self, request):
        file_app_services = fas(self.user_access_controller, self.log)
        # get id of file from request
        fobj = file_app_services.get_file(request.user, request.data["file_id"])
        response = file_app_services.file_download_from_s3(
            request.user, fobj.location, fobj.origin_name
        )
        return response
