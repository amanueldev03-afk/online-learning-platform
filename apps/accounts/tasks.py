import hashlib

from celery import shared_task

from .models import EmailVerificationToken
from .email_services import send_verification_email

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_verification_email_task(
    self,
    user_id,
    raw_token,
):
    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    verification = (
        EmailVerificationToken.objects
        .select_related("user")
        .filter(
            user_id=user_id,
            token_hash=token_hash,
            used_at__isnull=True,
        )
        .first()
    )

    if not verification:
        return {
            "status": "skipped",
            "reason": "verification token is invalid",
        }

    send_verification_email(
        verification.user,
        raw_token,
    )

    return {
        "status": "sent",
        "user_id": user_id,
    }