import os
import json
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv

load_dotenv()

class PushService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.vapid_public_key = os.environ.get("VAPID_PUBLIC_KEY")
        self.vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
        self.admin_email = "admin@10d.ai" # Required by pywebpush

    def save_subscription(self, user_id, subscription_data):
        """Saves a PWA subscription to Supabase"""
        try:
            data = {
                "user_id": user_id,
                "subscription_data": subscription_data
            }
            # Use upsert to avoid duplicates
            self.db.client.table("push_subscriptions").upsert(data, on_conflict="user_id, subscription_data").execute()
            return True
        except Exception as e:
            print(f"[PUSH] Error saving subscription: {e}", flush=True)
            return False

    def send_notification(self, user_id, title, message, url=None):
        """Sends a push notification to all subscriptions of a user"""
        try:
            subscriptions = self.db.client.table("push_subscriptions").select("subscription_data").eq("user_id", user_id).execute()
            
            if not subscriptions.data:
                return 0

            count = 0
            payload = json.dumps({
                "title": title,
                "body": message,
                "url": url or "/banca",
                "icon": "/logo10D.png"
            })

            for sub in subscriptions.data:
                try:
                    webpush(
                        subscription_info=sub["subscription_data"],
                        data=payload,
                        vapid_private_key=self.vapid_private_key,
                        vapid_claims={"sub": f"mailto:{self.admin_email}"}
                    )
                    count += 1
                except WebPushException as ex:
                    print(f"[PUSH] Push failed: {ex}", flush=True)
                    # If subscription is gone (410 Gone), we should remove it
                    if ex.response is not None and ex.response.status_code in [410, 404]:
                        self._remove_subscription(user_id, sub["subscription_data"])
            
            return count
        except Exception as e:
            print(f"[PUSH] Error sending notification: {e}", flush=True)
            return 0

    def _remove_subscription(self, user_id, subscription_data):
        """Clean up dead subscriptions"""
        try:
            self.db.client.table("push_subscriptions").delete().eq("user_id", user_id).eq("subscription_data", subscription_data).execute()
        except:
            pass
