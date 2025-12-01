from fastapi import File, Form, HTTPException, UploadFile


class PartInputValidator:
    def __init__(
        self,
        part_image_raw: str | None = File(default=None),
        part_image_file: UploadFile | None = File(default=None),  # noqa: B008
        part_text_query: str | None = Form(default=None),
    ):
        if isinstance(part_image_file, UploadFile):
            self.part_image = part_image_file
        else:
            self.part_image = None

        self.part_text_query = part_text_query

        if not self.part_image and not self.part_text_query:
            raise HTTPException(status_code=400, detail="Either part_image or part_text_query must be provided.")
