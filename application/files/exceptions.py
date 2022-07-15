from dataclasses import dataclass

@dataclass(frozen=True)
class FileException(Exception):
    item: str
    message: str

    def __str__(self):
        return "{}: {}".format(self.item, self.message)

@dataclass(frozen=True)
class FileUploadException(Exception):
    item: str
    message: str

    def __str__(self):
        return "{}: {}".format(self.item, self.message) 
        