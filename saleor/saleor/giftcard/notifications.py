from typing import TYPE_CHECKING

from ..account.notifications import get_default_user_payload
from ..core.notification.utils import get_site_context
from ..core.notify_events import NotifyEventType

if TYPE_CHECKING:
    from .models import GiftCard


def send_gift_card_notification(
    requester_user,
    app,
    customer_user,
    email,
    gift_card,
    manager,
    channel_slug,
    *,
    resending
):
    """Trigger sending a gift card notification for the given recipient."""
    payload = {
        "gift_card": get_default_gift_card_payload(gift_card),
        "user": get_default_user_payload(customer_user) if customer_user else None,
        "requester_user_id": requester_user.id if requester_user else None,
        "requester_app_id": app.id if app else None,
        "recipient_email": email,
        "resending": resending,
        **get_site_context(),
    }
    manager.notify(
        NotifyEventType.SEND_GIFT_CARD, payload=payload, channel_slug=channel_slug
    )


def get_default_gift_card_payload(gift_card: "GiftCard"):
    return {
        "id": gift_card.id,
        "code": gift_card.code,
        "balance": gift_card.current_balance_amount,
        "currency": gift_card.currency,
    }
