# python imports
import typing
import json
import uuid

# django imports

# app imports
from domain.users.models import User
from scripts.db_content_manager.data_generation_helpers import create_string

# local imports
from .models import File, FileID, FileFactory

# TODO: set a constant random seed to get repeatable results
def generate_random_file(user: User) -> File:
    return FileFactory.build_entity_with_id(
        user.id,
        "Test Title",
        "Test Description",
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


def generate_random_files(user: User, num_of_files: int) -> typing.List[File]:
    files = []
    for _ in range(num_of_files):
        files.append(generate_random_file(user))
    return files


def create_file_data() -> dict:
    """
    Returns a dict to be used in instance creation or for testing purposes
    """

    random_str = create_string()
    data = dict(
        id=FileID(uuid.uuid4()).value,
        uploader="c13cce88-42e3-40a1-9402-abf7e2f0a297",
        title=f"Title {random_str}",
        description=f"Description {random_str}",
        origin_name=f"{random_str}.png",
        location=f"https://www.files.com/{random_str}",
        status="active",
    )

    return data


class TestFileFactory():
    def create_files(n: int = 5):

        file_counter = 0
        created_file_ids = []

        for _ in range(n):
            data = create_file_data()
            new_instance = File(**data)
            new_instance.save()

            created_file_ids.append(FileID(new_instance.id))
            file_counter += 1

        print(
            f'Created {file_counter} total files.')

        return created_file_ids