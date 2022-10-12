# type: ignore

import asyncio
import discord
from discord.ext import commands

import logging; log = logging.getLogger()
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub import EventSub
from toolbox import S as Object
import asyncio

from .. import AutoModPluginBlueprint, ShardedBotInstance
from ...types import Embed



class AlertsPlugin(AutoModPluginBlueprint):
    """Plugin for alerts"""
    def __init__(
        self, 
        bot: ShardedBotInstance
    ) -> None:
        super().__init__(bot)
        self._event_sub: EventSub = None # for type hint
        self.bot.loop.create_task(self._init_twitch_event_sub())


    def cog_unload(
        self
    ) -> None:
        try:
            self._event_sub.stop()
        except Exception:
            pass


    async def _init_twitch_event_sub(
        self
    ) -> None:
        twitch = Twitch(
            self.config.twitch_app_id, 
            self.config.twitch_secret
        ); twitch.authenticate_app([])

        sub = EventSub(
            self.config.twitch_callback_url,  
            self.config.twitch_app_id,
            8080,
            twitch
        ); sub.wait_for_subscription_confirm = False
        setattr(self, "_event_sub", sub)

        self._event_sub.unsubscribe_all()
        self._event_sub.start()

        #max = Object(list((twitch.get_users(logins=["trymacs"])).values())[0][0])
        me = Object(list((twitch.get_users(logins=["xpaul2k"])).values())[0][0])
        #self._event_sub.listen_stream_online(max.id, self.on_live)
        self._event_sub.listen_channel_update(me.id, self.on_live)


    async def on_live(
        self,
        data: dict
    ) -> None:
        print(data)
        c = self.bot.get_channel(697830154113777695)
        asyncio.run_coroutine_threadsafe(
            c.send("Works!"),
            loop=self.bot.loop
        )
        

async def setup(bot) -> None: await bot.register_plugin(AlertsPlugin(bot))