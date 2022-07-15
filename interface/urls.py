from rest_framework_nested import routers

from . import views

file_pattern = r"file"
file_upload_pattern = r"file/upload"
file_download_pattern = r"file/download"

router = routers.SimpleRouter()
router.register(file_upload_pattern, views.FileUploadViewSet, basename="file/upload")
router.register(
    file_download_pattern, views.FileDownloadViewSet, basename="file/download"
)
router.register(file_pattern, views.FileViewSet, basename="file")
