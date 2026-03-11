"""
Uploads resumes to Supabase Storage inside:
resumes/users/<user_id>/<uuid>.docx

Returns a signed URL valid for 7 days.
"""

import os
from uuid import uuid4
from services.supabase_client import supabase
from services.auth_manager import auth

BUCKET_NAME = "resumes"


def upload_resume(file_path: str) -> str | None:
    """
    Uploads a resume for the authenticated user.
    Creates a structured folder:
        resumes/users/<user_id>/<uuid>.docx

    Returns:
        str | None — a signed URL (valid 7 days) or None on fail.
    """

    # ------------------------------------------------------------
    # 1. Validate authenticated user
    # ------------------------------------------------------------
    user = auth.get_user()
    if not user:
        print("[UPLOAD ERROR] No authenticated user.")
        return None

    user_id = user.id  # Ensure this matches AuthManager's return type

    # ------------------------------------------------------------
    # 2. Prepare file path + MIME type
    # ------------------------------------------------------------
    ext = os.path.splitext(file_path)[1]
    uuid_name = f"{uuid4()}{ext}"
    storage_key = f"users/{user_id}/{uuid_name}"

    # Auto-detect content type
    mime_type = (
        "application/pdf"
        if ext.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    try:
        # ------------------------------------------------------------
        # 3. Read file contents
        # ------------------------------------------------------------
        with open(file_path, "rb") as f:
            data = f.read()

        # ------------------------------------------------------------
        # 4. Upload to Supabase Storage
        # ------------------------------------------------------------
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_key,
            data,
            file_options={"content-type": mime_type},
        )

        signed = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            storage_key,
            expires_in=60 * 60 * 24 * 7,
        )

        return signed.signed_url

    except Exception as e:
        print("[UPLOAD EXCEPTION]", e)
        return None
