"""
Supabase Resume Uploader
--------------------------------------

Uploads resumes to:
    resumes/users/<user_id>/<uuid>.<ext>

Returns:
    A signed URL valid for 7 days, or None on failure.
"""

import os
from uuid import uuid4

from services.supabase_client import supabase
from services.auth_manager import auth

BUCKET_NAME = "resumes"


def upload_resume(file_path: str) -> str | None:
    """
    Uploads a resume for the authenticated user.
    Returns a signed URL (valid 7 days) or None.
    """

    # 1. Validate the user
    user = auth.get_user()
    if not user:
        print("[UPLOAD ERROR] No authenticated user.")
        return None

    user_id = user.id

    # 2. Validate the file
    if not os.path.isfile(file_path):
        print(f"[UPLOAD ERROR] File not found: {file_path}")
        return None

    ext = os.path.splitext(file_path)[1].lower()
    uuid_name = f"{uuid4()}{ext}"
    storage_key = f"users/{user_id}/{uuid_name}"

    mime_type = (
        "application/pdf"
        if ext == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    try:
        # 3. Read file data
        with open(file_path, "rb") as file:
            data = file.read()

        # 4. Upload file
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_key,
            data,
            file_options={"content-type": mime_type},
        )

        # Handle error response (dict-style API)
        if isinstance(result, dict) and result.get("error"):
            print("[UPLOAD FAILED]", result["error"])
            return None

        # 5. Create a signed URL (valid 7 days)
        signed = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            storage_key,
            expires_in=60 * 60 * 24 * 7,
        )

        # Handle both Supabase client response styles
        if hasattr(signed, "signed_url"):
            return signed.signed_url
        if isinstance(signed, dict):
            return signed.get("signedURL")

        return None

    except Exception as e:
        print("[UPLOAD EXCEPTION]", e)
        return None