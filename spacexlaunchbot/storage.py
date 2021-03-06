import logging
import pickle  # nosec
from copy import deepcopy
from dataclasses import dataclass
from typing import Tuple, Dict

from .notifications import NotificationType


@dataclass
class SubscriptionOptions:
    """A dataclass for holding channel subscription options."""

    notification_type: NotificationType
    launch_mentions: str


class DataStore:
    """A class to handle storing bot data.

    Dynamically loads from pickled file if possible.

    All methods that either return or take mutable objects as parameters make a deep
        copy of said object(s) so that changes cannot be made outside the instance.

    Immutable object references:
     - https://stackoverflow.com/a/23715872/6396652
     - https://stackoverflow.com/a/986145/6396652
    """

    def __init__(self, pickle_file_path: str):
        self._pickle_file_path = pickle_file_path

        # Map of {subscribed channel id: SubscriptionOptions}.
        self._subscribed_channels: Dict[int, SubscriptionOptions] = {}
        # Boolean indicating if a launch notification has been sent for the current
        # schedule.
        self._launch_embed_for_current_schedule_sent: bool = False
        # A dict of the most previously sent schedule embed (for comparison).
        self._previous_schedule_embed_dict: Dict = {}

        try:
            with open(self._pickle_file_path, "rb") as f_in:
                tmp = pickle.load(f_in)  # nosec
            self.__dict__.update(tmp)
            logging.info(f"Updated self.__dict__ from {self._pickle_file_path}")
        except FileNotFoundError:
            logging.info(f"Could not find file at location: {self._pickle_file_path}")

    def save(self) -> None:
        # Idea from https://stackoverflow.com/a/2842727/6396652.
        # pylint: disable=line-too-long
        to_dump = {
            "_subscribed_channels": self._subscribed_channels,
            "_launch_embed_for_current_schedule_sent": self._launch_embed_for_current_schedule_sent,
            "_previous_schedule_embed_dict": self._previous_schedule_embed_dict,
        }
        with open(self._pickle_file_path, "wb") as f_out:
            pickle.dump(to_dump, f_out, protocol=pickle.HIGHEST_PROTOCOL)

    def get_notification_task_vars(self) -> Tuple[bool, Dict]:
        return (
            self._launch_embed_for_current_schedule_sent,
            deepcopy(self._previous_schedule_embed_dict),
        )

    def set_notification_task_vars(
        self,
        launch_embed_for_current_schedule_sent: bool,
        previous_schedule_embed_dict: Dict,
    ) -> None:
        self._launch_embed_for_current_schedule_sent = (
            launch_embed_for_current_schedule_sent
        )
        self._previous_schedule_embed_dict = deepcopy(previous_schedule_embed_dict)
        self.save()

    def add_subbed_channel(
        self, channel_id: int, notif_type: NotificationType, launch_mentions: str,
    ) -> bool:
        """Add a channel to subscribed channels.

        Args:
            channel_id: The channel to add.
            notif_type: The type of subscription.
            launch_mentions: The mentions for launch notifications.

        """
        if channel_id not in self._subscribed_channels:
            self._subscribed_channels[channel_id] = SubscriptionOptions(
                notif_type, launch_mentions
            )
            self.save()
            return True
        return False

    def get_subbed_channels(self) -> Dict[int, SubscriptionOptions]:
        return deepcopy(self._subscribed_channels)

    def remove_subbed_channel(self, channel_id: int) -> bool:
        if channel_id in self._subscribed_channels:
            del self._subscribed_channels[channel_id]
            self.save()
            return True
        return False

    @property
    def subbed_channels_count(self) -> int:
        return len(self._subscribed_channels)
