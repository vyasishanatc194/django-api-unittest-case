# python imports
from io import BytesIO
import os
import logging
from PIL import Image
import copy

# django imports
from django.db.models.query import QuerySet
from django.http import FileResponse
from django.utils.crypto import get_random_string
from storages.backends.s3boto3 import S3Boto3Storage
from rest_framework import serializers
from django.conf import settings

# app imports
from domain.files.services import FileServices
from domain.files.models import File, FileFactory
from interface.storages.custom_storage import MediaStorage
from application.app_access_control.services import UserAccessController
from application.files.exceptions import FileUploadException
from infrastructure.logger.models import AttributeLogger

# local imports
from .tests_helper import create_test_file, create_file_with_bytes

logger = AttributeLogger(logging.getLogger(__name__))


class FileAppServices:
    def __init__(self, user_access_controller: UserAccessController, log: AttributeLogger):
        self.user_access_controller = user_access_controller
        self.log = log
        self.file_services = FileServices(log)

    def get_file(self, user, id) -> QuerySet:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        return self.file_services.get_file_repo().get(id=id)

    def list_files(self, user) -> QuerySet:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        return self.file_services.get_file_repo().all()

    def delete_file_soft(self, id) -> QuerySet:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        file = self.file_services.get_file_repo().get(id=id)
        file.status = "deactivated"
        file.save()
        return file

    def file_validation(self, file_obj, file_type=None, size_soft_limit_mb=None):
        size_hard_limit_mb = 50
        content_type = self.get_mime_type(file_obj.name)
        if file_type != "" and file_type != None:
            if file_obj.content_type != file_type:
                logger.warning(
                    "File ( {} ) does not match file_type {}.".format(
                        file_obj.content_type, file_type
                    )
                )
                raise serializers.ValidationError(
                    "File ( {} ) does not match file_type {}.".format(
                        file_obj.content_type, file_type
                    )
                )
        if file_obj.content_type != content_type["mime_type"]:
            logger.warning(
                "File type not permitted - {} .  ".format(file_obj.content_type)
            )
            raise serializers.ValidationError(
                "File type not permitted - {}.".format(file_obj.content_type)
            )
        if size_soft_limit_mb != "" and size_soft_limit_mb != None:
            if (int(size_soft_limit_mb) * 1000000) < file_obj.size:
                logger.warning(
                    "File size not permitted - {} MB > size_soft_limit ".format(
                        file_obj.size
                    )
                )
                raise serializers.ValidationError(
                    "File not permitted - {} MB > size_soft_limit.".format(
                        file_obj.size
                    )
                )
        if file_obj.size > (int(size_hard_limit_mb) * 1000000):
            logger.warning(
                "File size not permitted - {} MB > size_hard_limit ".format(
                    file_obj.size
                )
            )
            raise serializers.ValidationError(
                "File size not permitted - {} MB > size_hard_limit.".format(
                    file_obj.size
                )
            )
        if content_type["mime_type"].split("/")[0] == "image":
            allowed_max_width = settings.MAX_PROFILE_PIC_WIDTH
            allowed_max_height = settings.MAX_PROFILE_PIC_HEIGHT
            image_height = self.build_meta_data(file_obj).get("height")
            image_width = self.build_meta_data(file_obj).get("width")
            if image_height > allowed_max_height or image_width > allowed_max_width:
                logger.warning(
                    "Image Height or Width not permitted - Height:{} Pixel, Width:{}Pixel > allowed_max_height: {} Pixel,  allowed_max_width: {} Pixel ".format(
                        image_height, image_width, allowed_max_height, allowed_max_width
                    )
                )
                raise serializers.ValidationError(
                    "Image Height or Width not permitted - Height:{} Pixel, Width:{}Pixel > allowed_max_height: {} Pixel,  allowed_max_width: {} Pixel ".format(
                        image_height, image_width, allowed_max_height, allowed_max_width
                    )
                )

    def file_upload_s3(self, user, file_obj, deepcopy=True) -> str:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        file_path_within_bucket = os.path.join(user.username, get_random_string(12))
        if(deepcopy):
            file_obj_copy = copy.deepcopy(file_obj)
        else: # added because of a pickle problem on terms and conditions, does not impact any module
            file_obj_copy = file_obj
        media_storage = MediaStorage()
        media_storage.save(file_path_within_bucket, file_obj_copy)
        file_url = media_storage.url(file_path_within_bucket)

        # return key of the s3 object
        return file_path_within_bucket

    def create_file_from_s3(self, user, file_obj, upload_key) -> File:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        validated_data = {
            "uploader": user.id,
            "title": "{} uploaded".format(file_obj.name),
            "description": "A file is uploaded to s3",
            "origin_name": file_obj.name,
            "location": upload_key,
            "status": "active",
            "meta_data":self.build_meta_data(file_obj),
        }
        fobj = self.create_file_from_dict(user, validated_data)
        return fobj

    def read_allowed_files(self, user, allowed_files, file_id):
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        file_obj = self.get_file(user, file_id)
        if file_obj is not None:
            content_type = self.get_mime_type(file_obj.origin_name)["mime_type"]
            if content_type in allowed_files:
                return self.read_file_from_s3(
                    user, file_obj.location, file_obj.origin_name
                )
            else:
                logger.warning(
                    "File type not permitted - {}.".format(file_obj.content_type)
                )
                raise serializers.ValidationError(
                    "File type not permitted - {}.".format(file_obj.content_type)
                )
        else:
            raise serializers.ValidationError(
                "file_id does not exist - {}.".format(file_id)
            )

    def read_file_from_s3(self, user, key, filename) -> S3Boto3Storage:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        media_storage = MediaStorage()
        read_file = media_storage.open(key)
        return read_file

    def file_delete_s3(self, user, key) -> bool:
        media_storage = MediaStorage()
        media_storage.delete(key)
        return True

    def file_download_from_s3(self, user, key, filename) -> FileResponse:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        media_storage = MediaStorage()
        download_file = media_storage.open(key)
        content_type = self.get_mime_type(filename)

        response = FileResponse(download_file, content_type=content_type)
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
        return response

    def create_file_from_dict(self, user, data: dict) -> File:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        title = data["title"]
        description = data["description"]
        origin_name = data["origin_name"]
        location = data["location"]
        status = data["status"]
        meta_data = data["meta_data"]

        data_file = FileFactory.build_entity_with_id(
            user.id, title, description, origin_name, location, status, meta_data
        )
        data_file.save()
        return data_file

    def update_file_from_dict(self, user, instance: File, data: dict) -> File:
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        # get file by id

        title = data["title"]
        description = data["description"]
        origin_name = data["origin_name"]
        location = data["location"]
        status = data["status"]
        meta_data = data["meta_data"]

        instance.update_entity(
            user.id, title, description, origin_name, location, status, meta_data
        )
        instance.save()
        return instance

    def get_mime_type(self, filename):
        # TODO:
        # Fetch controller by user id
        # If controller does not exist propagate or handle exception
        # get file by id
        mimeTypes = {
            "323": "text/h323",
            "acx": "application/internet-property-stream",
            "ai": "application/postscript",
            "aif": "audio/x-aiff",
            "aifc": "audio/x-aiff",
            "aiff": "audio/x-aiff",
            "asf": "video/x-ms-asf",
            "asr": "video/x-ms-asf",
            "asx": "video/x-ms-asf",
            "au": "audio/basic",
            "avi": "video/x-msvideo",
            "axs": "application/olescript",
            "bas": "text/plain",
            "bcpio": "application/x-bcpio",
            "bin": "application/octet-stream",
            "bmp": "image/bmp",
            "c": "text/plain",
            "cat": "application/vnd.ms-pkiseccat",
            "cdf": "application/x-cdf",
            "cer": "application/x-x509-ca-cert",
            "class": "application/octet-stream",
            "clp": "application/x-msclip",
            "cmx": "image/x-cmx",
            "cod": "image/cis-cod",
            "cpio": "application/x-cpio",
            "crd": "application/x-mscardfile",
            "crl": "application/pkix-crl",
            "crt": "application/x-x509-ca-cert",
            "csh": "application/x-csh",
            "css": "text/css",
            "csv": "text/csv",
            "dcr": "application/x-director",
            "der": "application/x-x509-ca-cert",
            "dir": "application/x-director",
            "dll": "application/x-msdownload",
            "dms": "application/octet-stream",
            "doc": "application/msword",
            "dot": "application/msword",
            "dvi": "application/x-dvi",
            "dxr": "application/x-director",
            "eps": "application/postscript",
            "etx": "text/x-setext",
            "evy": "application/envoy",
            "exe": "application/octet-stream",
            "fif": "application/fractals",
            "flr": "x-world/x-vrml",
            "gif": "image/gif",
            "gtar": "application/x-gtar",
            "gz": "application/x-gzip",
            "h": "text/plain",
            "hdf": "application/x-hdf",
            "hlp": "application/winhlp",
            "hqx": "application/mac-binhex40",
            "hta": "application/hta",
            "htc": "text/x-component",
            "htm": "text/html",
            "html": "text/html",
            "htt": "text/webviewhtml",
            "ico": "image/x-icon",
            "ief": "image/ief",
            "iii": "application/x-iphone",
            "ins": "application/x-internet-signup",
            "isp": "application/x-internet-signup",
            "json": "application/json",
            "jfif": "image/pipeg",
            "jpe": "image/jpeg",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "js": "application/x-javascript",
            "latex": "application/x-latex",
            "lha": "application/octet-stream",
            "lsf": "video/x-la-asf",
            "lsx": "video/x-la-asf",
            "lzh": "application/octet-stream",
            "m13": "application/x-msmediaview",
            "m14": "application/x-msmediaview",
            "m3u": "audio/x-mpegurl",
            "man": "application/x-troff-man",
            "mdb": "application/x-msaccess",
            "me": "application/x-troff-me",
            "mht": "message/rfc822",
            "mhtml": "message/rfc822",
            "mid": "audio/mid",
            "mny": "application/x-msmoney",
            "mov": "video/quicktime",
            "movie": "video/x-sgi-movie",
            "mp2": "video/mpeg",
            "mp3": "audio/mpeg",
            "mpa": "video/mpeg",
            "mpe": "video/mpeg",
            "mpeg": "video/mpeg",
            "mpg": "video/mpeg",
            "mpp": "application/vnd.ms-project",
            "mpv2": "video/mpeg",
            "ms": "application/x-troff-ms",
            "mvb": "application/x-msmediaview",
            "nws": "message/rfc822",
            "oda": "application/oda",
            "p10": "application/pkcs10",
            "p12": "application/x-pkcs12",
            "p7b": "application/x-pkcs7-certificates",
            "p7c": "application/x-pkcs7-mime",
            "p7m": "application/x-pkcs7-mime",
            "p7r": "application/x-pkcs7-certreqresp",
            "p7s": "application/x-pkcs7-signature",
            "pbm": "image/x-portable-bitmap",
            "pdf": "application/pdf",
            "pfx": "application/x-pkcs12",
            "pgm": "image/x-portable-graymap",
            "pko": "application/ynd.ms-pkipko",
            "pma": "application/x-perfmon",
            "pmc": "application/x-perfmon",
            "pml": "application/x-perfmon",
            "pmr": "application/x-perfmon",
            "pmw": "application/x-perfmon",
            "png": "image/png",
            "pnm": "image/x-portable-anymap",
            "pot": "application/vnd.ms-powerpoint",
            "ppm": "image/x-portable-pixmap",
            "pps": "application/vnd.ms-powerpoint",
            "ppt": "application/vnd.ms-powerpoint",
            "prf": "application/pics-rules",
            "ps": "application/postscript",
            "pub": "application/x-mspublisher",
            "qt": "video/quicktime",
            "ra": "audio/x-pn-realaudio",
            "ram": "audio/x-pn-realaudio",
            "ras": "image/x-cmu-raster",
            "rgb": "image/x-rgb",
            "rmi": "audio/mid",
            "roff": "application/x-troff",
            "rtf": "application/rtf",
            "rtx": "text/richtext",
            "scd": "application/x-msschedule",
            "sct": "text/scriptlet",
            "setpay": "application/set-payment-initiation",
            "setreg": "application/set-registration-initiation",
            "sh": "application/x-sh",
            "shar": "application/x-shar",
            "sit": "application/x-stuffit",
            "snd": "audio/basic",
            "spc": "application/x-pkcs7-certificates",
            "spl": "application/futuresplash",
            "src": "application/x-wais-source",
            "sst": "application/vnd.ms-pkicertstore",
            "stl": "application/vnd.ms-pkistl",
            "stm": "text/html",
            "svg": "image/svg+xml",
            "sv4cpio": "application/x-sv4cpio",
            "sv4crc": "application/x-sv4crc",
            "t": "application/x-troff",
            "tar": "application/x-tar",
            "tcl": "application/x-tcl",
            "tex": "application/x-tex",
            "texi": "application/x-texinfo",
            "texinfo": "application/x-texinfo",
            "tgz": "application/x-compressed",
            "tif": "image/tiff",
            "tiff": "image/tiff",
            "tr": "application/x-troff",
            "trm": "application/x-msterminal",
            "tsv": "text/tab-separated-values",
            "txt": "text/plain",
            "uls": "text/iuls",
            "ustar": "application/x-ustar",
            "vcf": "text/x-vcard",
            "vrml": "x-world/x-vrml",
            "wav": "audio/x-wav",
            "wcm": "application/vnd.ms-works",
            "wdb": "application/vnd.ms-works",
            "wks": "application/vnd.ms-works",
            "wmf": "application/x-msmetafile",
            "wps": "application/vnd.ms-works",
            "wri": "application/x-mswrite",
            "wrl": "x-world/x-vrml",
            "wrz": "x-world/x-vrml",
            "xaf": "x-world/x-vrml",
            "xbm": "image/x-xbitmap",
            "xla": "application/vnd.ms-excel",
            "xlc": "application/vnd.ms-excel",
            "xlm": "application/vnd.ms-excel",
            "xls": "application/vnd.ms-excel",
            "xlsx": "vnd.ms-excel",
            "xlt": "application/vnd.ms-excel",
            "xlw": "application/vnd.ms-excel",
            "xof": "x-world/x-vrml",
            "xpm": "image/x-xpixmap",
            "xwd": "image/x-xwindowdump",
            "z": "application/x-compress",
            "zip": "application/zip",
        }

        extension = filename.split(".")[-1]
        resp = dict()
        resp["file_extension"] = extension
        resp["mime_type"] = mimeTypes[extension]
        return resp

    def build_meta_data(self, file_obj) -> dict:
        """
        read meta data for uploaded file
        """
        meta_data = dict()
        if type(file_obj) == BytesIO:
            filesize_in_bytes = file_obj.getbuffer().nbytes
        else:
            filesize_in_bytes = file_obj.size
        mime_type = self.get_mime_type(filename=file_obj.name)["mime_type"]
        meta_data["mime_type"] = mime_type
        meta_data["filesize_in_bytes"] = filesize_in_bytes
        if mime_type.split("/")[0] == "image":
            with Image.open(file_obj) as img:
                width, height = img.size
            meta_data["width"] = width
            meta_data["height"] = height
        return meta_data

    def upload_file_from_terminal(self, user, file_obj) -> str:
        file_path_within_bucket = os.path.join(user.username, get_random_string(12))
        media_storage = MediaStorage()
        media_storage.save(file_path_within_bucket, file_obj)
        file_url = media_storage.url(file_path_within_bucket)

        validated_data = {
            "uploader": user.id,
            "title": "{} uploaded".format(file_obj.name),
            "description": "A file is uploaded to s3",
            "origin_name": file_obj.name,
            "location": file_path_within_bucket,
            "status": "active",
            "meta_data":"",
        }
        fobj = self.create_file_from_dict(user, validated_data)
        return fobj

    def upload_file(self, data):
        user = self.user_access_controller.get_user()

        try:
            self.file_validation(
                data["upload_file"], data["file_type"], data["size_soft_limit_mb"]
            )
            upload_key = self.file_upload_s3(
                user, 
                data["upload_file"]
            )
            file_object = self.create_file_from_s3(
                user, 
                data["upload_file"], 
                upload_key
            )
            return upload_key, file_object

        except:
            FileUploadException(
                "file-upload-exception",
                "The specified file cannot be uploaded"
            )
