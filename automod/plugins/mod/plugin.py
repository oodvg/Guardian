# type: ignore

import json
import discord
from discord.ext import commands

import datetime
import asyncio
import logging; log = logging.getLogger()
import datetime
from typing import Union, Callable, Literal
import pytz; UTC = pytz.UTC

from ..warn.plugin import WarnPlugin, ShardedBotInstance
from .._processor import LogProcessor, ActionProcessor, DMProcessor
from ...types import Duration, Embed, E
from ...views import ConfirmView, ActionedView
from ...schemas import Mute, Tempban



ACTIONS = {
    "ban": {
        "action": "ban",
        "log": "banned"
    },
    "softban": {
        "action": "ban",
        "log": "softbanned"
    },
    "hackban": {
        "action": "ban",
        "log": "hackbanned"
    },
    "kick": {
        "action": "kick",
        "log": "kicked"
    },
}


DELETE_MESSAGES_ARG = Literal[
    "None",
    "Previous 24 hours",
    "Previous 3 days",
    "Previous 7 days",
]
DELETE_MESSAGES_ARG_MAP = {
    "none": 0,
    "previous 24 hours": 1,
    "previous 3 days": 3,
    "previous 7 days": 7
}


class ModerationPlugin(WarnPlugin):
    """Plugin for all moderation commands"""
    def __init__(self, bot: ShardedBotInstance) -> None:
        super().__init__(bot)
        self.log_processor = LogProcessor(bot)
        self.action_processor = ActionProcessor(bot)
        self.dm_processor = DMProcessor(bot)
        for f in ["unmutes", "unbans"]: self.bot.loop.create_task((getattr(self, f"handle_{f}"))())


    async def handle_unmutes(self) -> None:
        while True:
            await asyncio.sleep(10)
            if len(list(self.db.mutes.find({}))) > 0:
                for mute in self.db.mutes.find():
                    if "until" in mute:
                        ending = mute["until"]
                    else:
                        ending = mute["ending"]

                    if ending < datetime.datetime.utcnow():
                        guild = self.bot.get_guild(int(mute["id"].split("-")[0]))
                        if guild != None:

                            t = guild.get_member(int(mute["id"].split("-")[1]))
                            if t == None:
                                t = "Unknown#0000"

                            await self.log_processor.execute(guild, "unmute", **{
                                "user": t,
                                "user_id": int(mute["id"].split("-")[1]),
                                "mod": guild.get_member(self.bot.user.id),
                                "mod_id": self.bot.user.id,
                                "reason": "Mute expired, automated by AutoMod"
                            })
                        self.db.mutes.delete(mute["id"])


    async def handle_unbans(self) -> None:
        while True:
            await asyncio.sleep(10)
            if len(list(self.db.tbans.find({}))) > 0:
                for ban in self.db.tbans.find():
                    if "until" in ban:
                        ending = ban["until"]
                    else:
                        ending = ban["ending"]

                    if ending < datetime.datetime.utcnow():
                        guild = self.bot.get_guild(int(ban["id"].split("-")[0]))
                        if guild != None:

                            t = guild.get_member(int(ban["id"].split("-")[1]))
                            if t == None:
                                t = "Unknown#0000"
                            else:
                                try:
                                    await guild.unban(user=t, reason="Tempban expired, automated by AutoMod")
                                except Exception:
                                    pass
                                else:
                                    self.bot.ignore_for_events.append(t.id)
                                
                            await self.log_processor.execute(guild, "tempunban", **{
                                "user": t,
                                "user_id": int(ban["id"].split("-")[1]),
                                "mod": guild.get_member(self.bot.user.id),
                                "mod_id": self.bot.user.id,
                                "reason": "Tempban expired, automated by AutoMod"
                            })
                        self.db.tbans.delete(ban["id"])


    async def clean_messages(
        self, 
        ctx: discord.Interaction, 
        amount: int, 
        check: Callable, 
        before: Union[datetime.datetime, discord.Message] = None, 
        after: Union[datetime.datetime, discord.Message] = None
    ) -> Union[str, Exception]: 
        try:
            msgs = [
                m async for m in ctx.channel.history(
                    limit=300, 
                    before=before if before != None else discord.Object(id=ctx.id),
                    after=after if after != None else None
                ) if check(m) == True and UTC.localize((datetime.datetime.now() - datetime.timedelta(days=14))) <= m.created_at
            ][:amount]
            await ctx.channel.delete_messages(msgs)
        except Exception as ex:
            return self.error(ctx, ex)
        else:
            if len(msgs) < 1:
                return self.locale.t(ctx.guild, "no_messages_found", _emote="NO"), {}
            else:
                return self.locale.t(ctx.guild, "cleaned", _emote="YES", amount=len(msgs), plural="" if len(msgs) == 1 else "s"), {}


    async def kick_or_ban(self, action: str, ctx: discord.Interaction, user: Union[discord.Member, discord.User], reason: str, **_) -> None:
        if not ctx.guild.chunked: await self.bot.chunk_guild(ctx.guild)

        if action != "hackban":
            if ctx.guild.get_member(user.id) == None:
                return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_in_server", _emote="NO"), 0), ephemeral=True)

        if not self.can_act(ctx.guild, ctx.user, user):
            return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "cant_act", _emote="NO"), 0), ephemeral=True)

        self.dm_processor.execute(
            ctx,
            "ban",
            user,
            **{
                "guild_name": ctx.guild.name,
                "reason": reason,
                "_emote": "HAMMER"
            }
        )

        try:
            func = getattr(ctx.guild, ACTIONS[action]["action"])
            if action.lower() == "kick":
                await func(user=user, reason=reason)
            else:
                await func(user=user, reason=reason, delete_message_days=_.get("delete_message_days", 0))
        except Exception as ex:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=ex), 0), ephemeral=True)
        else:
            self.bot.ignore_for_events.append(user.id)
            if action == "softban":
                try:
                    await ctx.guild.unban(user=user)
                except Exception as ex:
                    await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=ex), 0), ephemeral=True)
                else:
                    self.bot.ignore_for_events.append(user.id)
                    await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "softbanned", _emote="YES", user=user, reason=reason), 1))
            
            await self.log_processor.execute(ctx.guild, action, **{
                "user": user,
                "user_id": user.id,
                "mod": ctx.user,
                "mod_id": ctx.user.id,
                "reason": reason,
                "channel_id": ctx.channel.id,
                "case": self.action_processor.new_case(action, ctx, ctx.user, user, reason)
            })
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, ACTIONS[action]["log"], _emote="YES", user=user, reason=reason), 1))


    @discord.app_commands.command(
        name="ban",
        description="🔨 Bans a user from the server"
    )
    @discord.app_commands.describe(
        user="The user you want to ban",
        reason="An optional reason for the ban",
        delete_messages="How many days of user messages to purge"
    )
    @discord.app_commands.default_permissions(ban_members=True)
    async def ban(self, ctx: discord.Interaction, user: discord.User, *, delete_messages: DELETE_MESSAGES_ARG = "None", reason: str = None) -> None:
        """
        ban_help
        examples:
        -ban @paul#0009 test
        -ban 543056846601191508
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await self.kick_or_ban("ban", ctx, user, reason, delete_message_days=DELETE_MESSAGES_ARG_MAP[delete_messages.lower()])
        else:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_banned", _emote="WARN"), 0), ephemeral=True)

    
    @discord.app_commands.command(
        name="unban",
        description="🔓 Unbans a user from the server"
    )
    @discord.app_commands.describe(
        user="The user you want to unban",
        reason="An optional reason for the ban"
    )
    @discord.app_commands.default_permissions(ban_members=True)
    async def unban(self, ctx: discord.Interaction, user: discord.User, *, reason: str = None) -> None:
        """
        unban_help
        examples:
        -unban 543056846601191508
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)
    
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_banned", _emote="WARN"), 0), ephemeral=True)
        else:
            try:
                await ctx.guild.unban(user=user, reason=reason)
            except Exception as ex:
                await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=ex), 0), ephemeral=True)
            else:
                self.bot.ignore_for_events.append(user.id)
                await self.log_processor.execute(ctx.guild, "unban", **{
                    "user": user,
                    "user_id": user.id,
                    "mod": ctx.user,
                    "mod_id": ctx.user.id,
                    "reason": reason,
                    "channel_id": ctx.channel.id,
                    "case": self.action_processor.new_case("unban", ctx, ctx.user, user, reason)
                })

                await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "unbanned", _emote="YES", user=user, reason=reason), 1))
            finally:
                if self.db.tbans.exists(f"{ctx.guild.id}-{user.id}"):
                    self.db.tbans.delete(f"{ctx.guild.id}-{user.id}")


    @discord.app_commands.command(
        name="softban",
        description="🔨 Softbans a user from the server (ban & unban)"
    )
    @discord.app_commands.describe(
        user="The user you want to ban",
        reason="An optional reason for the ban",
        delete_messages="How many days of user messages to purge"
    )
    @discord.app_commands.default_permissions(ban_members=True)
    async def softban(self, ctx: discord.Interaction, user: discord.User, *, delete_messages: DELETE_MESSAGES_ARG = "None", reason: str = None) -> None:
        """
        softban_help
        examples:
        -softban @paul#0009 test
        -softban 543056846601191508
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await self.kick_or_ban("softban", ctx, user, reason, delete_message_days=DELETE_MESSAGES_ARG_MAP[delete_messages.lower()])
        else:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_banned", _emote="WARN"), 0), ephemeral=True)


    @discord.app_commands.command(
        name="forceban",
        description="🔨 Bans a user from the server (even if they aren't in the server)"
    )
    @discord.app_commands.describe(
        user="The user you want to ban",
        reason="An optional reason for the ban",
        delete_messages="How many days of user messages to purge"
    )
    @discord.app_commands.default_permissions(ban_members=True)
    async def hackban(self, ctx: discord.Interaction, user: discord.User, *, delete_messages: DELETE_MESSAGES_ARG = "None", reason: str = None) -> None:
        """
        hackban_help
        examples:
        -hackban @paul#0009 test
        -hackban 543056846601191508
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await self.kick_or_ban("hackban", ctx, user, reason, delete_message_days=DELETE_MESSAGES_ARG_MAP[delete_messages.lower()])
        else:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_banned", _emote="WARN"), 0), ephemeral=True)


    @discord.app_commands.command(
        name="tempban",
        description="🔨 Temporarily bans a user from the server"
    )
    @discord.app_commands.describe(
        user="The user you want to ban",
        length="10m, 2h, 1d",
        reason="An optional reason for the ban",
        delete_messages="How many days of user messages to purge"
    )
    @discord.app_commands.default_permissions(ban_members=True)
    async def tempban(self, ctx: discord.Interaction, user: discord.User, length: str, *, delete_messages: DELETE_MESSAGES_ARG = "None", reason: str = None) -> None:
        """
        tempban_help
        examples:
        -tempban @paul#0009 5d test
        -tempban 543056846601191508 7d
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)

        try:
            length = await Duration().convert(ctx, length)
        except Exception as ex:
            return self.error(ctx, ex)
        else:
            if length.unit == None: length.unit = "m"
            if not ctx.guild.chunked: await self.bot.chunk_guild(ctx.guild)

            if not self.can_act(ctx.guild, ctx.user, user):
                return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "cant_act", _emote="NO"), 0), ephemeral=True)

            try:
                seconds = length.to_seconds(ctx)
            except Exception as ex:
                return self.error(ctx, ex)

            try:
                await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                _id = f"{ctx.guild.id}-{user.id}"
                if self.db.tbans.exists(_id):

                    async def confirm(i):
                        until = (self.db.tbans.get(_id, "until") + datetime.timedelta(seconds=seconds))
                        self.db.tbans.update(_id, "until", until)

                        await i.response.edit_message(
                            content=self.locale.t(ctx.guild, "tempban_extended", _emote="YES", user=user, until=f"<t:{round(until.timestamp())}>", reason=reason), 
                            embed=None, 
                            view=None
                        )

                        self.dm_processor.execute(
                            ctx,
                            "tempban",
                            user,
                            **{
                                "guild_name": ctx.guild.name,
                                "until": f"<t:{round(until.timestamp())}>",
                                "reason": reason,
                                "_emote": "HAMMER"
                            }
                        )

                        await self.log_processor.execute(ctx.guild, "tempban_extended", **{
                            "mod": ctx.user, 
                            "mod_id": ctx.user.id,
                            "user": user,
                            "user_id": user.id,
                            "until": f"<t:{round(until.timestamp())}>",
                            "reason": reason,
                            "channel_id": ctx.channel.id,
                            "case": self.action_processor.new_case("tempban extended", ctx, ctx.user, user, reason, until=until)
                        })
                        return

                    async def cancel(i):
                        e = Embed(
                            ctx,
                            description=self.locale.t(ctx.guild, "aborting")
                        )
                        await i.response.edit_message(embed=e, view=None)

                    async def timeout():
                        e = Embed(
                            ctx,
                            description=self.locale.t(ctx.guild, "aborting")
                        )
                        try:
                            await ctx.followup.send(embed=e, view=None)
                        except Exception:
                            pass

                    def check(i):
                        return i.user.id == ctx.user.id

                    e = Embed(
                        ctx,
                        description=self.locale.t(ctx.guild, "already_tempbanned_description")
                    )
                    await ctx.response.send_message(embed=e, view=ConfirmView(self.bot, ctx.guild.id, on_confirm=confirm, on_cancel=cancel, on_timeout=timeout,check=check))
                else:
                    if seconds >= 1:
                        self.dm_processor.execute(
                            ctx,
                            "tempban",
                            user,
                            **{
                                "guild_name": ctx.guild.name,
                                "until": f"<t:{round(until.timestamp())}>",
                                "reason": reason,
                                "_emote": "HAMMER"
                            }
                        )
                        
                        try:
                            await ctx.guild.ban(
                                user=user, 
                                reason=f"{reason} | {length}{length.unit}",
                                delete_message_days=DELETE_MESSAGES_ARG_MAP[delete_messages.lower()]
                            )
                        except Exception as ex:
                            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=ex), 0), ephemeral=True)
                        else:
                            self.bot.ignore_for_events.append(user.id)
                            until = (datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds))
                            self.db.tbans.insert(Tempban(ctx.guild.id, user.id, until))


                            await self.log_processor.execute(ctx.guild, "tempban", **{
                                "mod": ctx.user, 
                                "mod_id": ctx.user.id,
                                "user": user,
                                "user_id": user.id,
                                "until": f"<t:{round(until.timestamp())}>",
                                "channel_id": ctx.channel.id,
                                "case": self.action_processor.new_case("tempban", ctx, ctx.user, user, reason, until=until),
                                "reason": reason
                            }) 

                            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "tempbanned", _emote="YES", user=user, until=f"<t:{round(until.timestamp())}>", reason=reason), 1))
                    else:
                        return self.error(ctx, commands.BadArgument("Number too small"))
            else:
                await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_banned", _emote="WARN"), 0), ephemeral=True)


    @discord.app_commands.command(
        name="kick",
        description="👢 Kicks a user from the server"
    )
    @discord.app_commands.describe(
        user="The user you want to kick",
        reason="An optional reason for the ban"
    )
    @discord.app_commands.default_permissions(kick_members=True)
    async def kick(self, ctx: discord.Interaction, user: discord.User, *, reason: str = None) -> None:
        """
        kick_help
        examples:
        -kick @paul#0009 test
        -kick 543056846601191508
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await self.kick_or_ban("kick", ctx, user, reason, delete_message_days=1)
        else:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_banned", _emote="WARN"), 0), ephemeral=True)


    @discord.app_commands.command(
        name="mute",
        description="🔇 Temporarily mutes a user"
    )
    @discord.app_commands.describe(
        user="The user you want to mute",
        length="10m, 2h, 1d",
        reason="An optional reason for the mute"
    )
    @discord.app_commands.default_permissions(manage_messages=True)
    async def mute(self, ctx: discord.Interaction, user: discord.Member, length: str, *, reason: str = None) -> None:
        """
        mute_help
        examples:
        -mute @paul#0009 10m test
        -mute 543056846601191508 1h
        """
        if reason == None: reason = self.bot.get_default_reason(ctx.guild)

        try:
            length = await Duration().convert(ctx, length)
        except Exception as ex:
            return self.error(ctx, ex)
        else:
            if length.unit == None: length.unit = "m"
            if not ctx.guild.chunked: await self.bot.chunk_guild(ctx.guild)

            if not self.can_act(ctx.guild, ctx.user, user):
                return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "cant_act", _emote="NO"), 0), ephemeral=True)

            try:
                seconds = length.to_seconds(ctx)
            except Exception as ex:
                return self.error(ctx, ex)

            _id = f"{ctx.guild.id}-{user.id}"
            if self.db.mutes.exists(_id):

                async def confirm(i):
                    until = (self.db.mutes.get(_id, "until") + datetime.timedelta(seconds=seconds))
                    self.db.mutes.update(_id, "until", until)

                    await i.response.edit_message(
                        content=self.locale.t(ctx.guild, "mute_extended", _emote="YES", user=user, until=f"<t:{round(until.timestamp())}>", reason=reason), 
                        embed=None, 
                        view=None
                    )

                    self.dm_processor.execute(
                        ctx,
                        "mute",
                        user,
                        **{
                            "guild_name": ctx.guild.name,
                            "until": f"<t:{round(until.timestamp())}>",
                            "reason": reason,
                            "_emote": "MUTE"
                        }
                    )

                    await self.log_processor.execute(ctx.guild, "mute_extended", **{
                        "mod": ctx.user, 
                        "mod_id": ctx.user.id,
                        "user": user,
                        "user_id": user.id,
                        "reason": reason,
                        "until": f"<t:{round(until.timestamp())}>",
                        "channel_id": ctx.channel.id,
                        "case": self.action_processor.new_case("mute extended", ctx, ctx.user, user, reason, until=until)
                    })
                    self.bot.handle_timeout(True, ctx.guild, user, until.isoformat())
                    return

                async def cancel(i):
                    e = Embed(
                    ctx,
                        description=self.locale.t(ctx.guild, "aborting")
                    )
                    await i.response.edit_message(embed=e, view=None)

                async def timeout():
                    e = Embed(
                        ctx,
                        description=self.locale.t(ctx.guild, "aborting")
                    )
                    try:
                        await ctx.followup.send(embed=e, view=None)
                    except Exception:
                        pass

                def check(i):
                    return i.user.id == ctx.user.id

                e = Embed(
                    ctx,
                    description=self.locale.t(ctx.guild, "already_muted_description")
                )
                message = await ctx.response.send_message(embed=e, view=ConfirmView(self.bot, ctx.guild.id, on_confirm=confirm, on_cancel=cancel, on_timeout=timeout,check=check))
            else:
                if seconds >= 1:
                    until = (datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds))
                    exc = self.bot.handle_timeout(True, ctx.guild, user, until.isoformat())
                    if exc != "":
                        try:
                            _temp_exc = json.loads(exc)
                        except Exception:
                            pass
                        else:
                            if int(_temp_exc["code"]) == 50013: exc = "The bot is missing permissions to mute this user"
                        finally:
                            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=exc), 0), ephemeral=True)
                    else:
                        self.db.mutes.insert(Mute(ctx.guild.id, user.id, until))

                        self.dm_processor.execute(
                            ctx,
                            "mute",
                            user,
                            **{
                                "guild_name": ctx.guild.name,
                                "until": f"<t:{round(until.timestamp())}>",
                                "reason": reason,
                                "_emote": "MUTE"
                            }
                        )

                        await self.log_processor.execute(ctx.guild, "mute", **{
                            "mod": ctx.user, 
                            "mod_id": ctx.user.id,
                            "user": user,
                            "user_id": user.id,
                            "reason": reason,
                            "until": f"<t:{round(until.timestamp())}>",
                            "channel_id": ctx.channel.id,
                            "case": self.action_processor.new_case("mute", ctx, ctx.user, user, reason, until=until)
                        }) 

                        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "muted", _emote="YES", user=user, until=f"<t:{round(until.timestamp())}>", reason=reason), 1))
                else:
                    return self.error(ctx, commands.BadArgument("Number too small"))


    @discord.app_commands.command(
        name="unmute",
        description="🔊 Unmutes a user"
    )
    @discord.app_commands.describe(
        user="The user you want to unmute"
    )
    @discord.app_commands.default_permissions(manage_messages=True)
    async def unmute(self, ctx: discord.Interaction, user: discord.Member) -> None:
        """
        unmute_help
        examples:
        -unmute @paul#0009
        -unmute 543056846601191508
        """
        _id = f"{ctx.guild.id}-{user.id}"
        if not self.db.mutes.exists(_id):
            return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_muted", _emote="NO"), 0), ephemeral=True)

        if (ctx.guild.me.guild_permissions.value & 0x10000000000) != 0x10000000000:
            if ctx.guild.me.guild_permissions.administrator == False: 
                return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "no_timeout_perms", _emote="NO"), 0), ephemeral=True)

        exc = self.bot.handle_timeout(False, ctx.guild, user, None)
        if exc != "":
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "fail", _emote="NO", exc=exc), 0), ephemeral=True)
        else:
            self.db.mutes.delete(_id)
            await self.log_processor.execute(ctx.guild, "manual_unmute", **{
                "mod": ctx.user, 
                "mod_id": ctx.user.id,
                "user": user,
                "user_id": user.id,
                "channel_id": ctx.channel.id,
                "case": self.action_processor.new_case("unmute", ctx, ctx.user, user, "Manual unmute")
            }) 

            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "unmuted", _emote="YES", user=user), 1))


    @discord.app_commands.command(
        name="purge",
        description="🧹 Purges messages from the channel"
    )
    @discord.app_commands.describe(
        amount="The amount of messages to delete (to check)",
        user="Only checks for messages by this user",
        content="Only checks for messages with the given content"
    )
    @discord.app_commands.default_permissions(manage_messages=True)
    async def clean_call(self, ctx: discord.Interaction, amount: int = 10, user: discord.User = None, content: str = None) -> None:
        """
        clean_all_help
        examples:
        -clean 25
        -clean 10 paul#0009
        -clean 50 paul#0009 bad words
        """
        if amount < 1: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "amount_too_small", _emote="NO"), 0), ephemeral=True)
        if amount > 100: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "amount_too_big", _emote="NO"), 0), ephemeral=True)
        
        if user == None and content == None:
            func = lambda _: _.pinned == False
        else:
            if user != None and content != None:
                func = lambda x: x.author.id == user.id and x.content.lower() == content.lower() and x.pinned == False
            elif user != None and content == None:
                func = lambda x: x.author.id == user.id and x.pinned == False
            else:
                func = lambda x: x.content.lower() == content.lower() and x.pinned == False
            
        await ctx.response.defer(thinking=True)
        msg, kwargs = await self.clean_messages(
            ctx,
            amount,
            func
        )
        msg = await ctx.followup.send(embed=E(msg, 1), **kwargs)
        if msg != None:
            try: await msg.delete(delay=5.0)
            except Exception: pass


    async def report(self, i: discord.Interaction, msg: discord.Message) -> None:
        if not self.can_act(
            msg.guild,
            i.user,
            msg.author
        ): return await i.response.send_message(
            embed=Embed(
                i,
                description=self.locale.t(msg.guild, "report_mod", _emote="NO")
            ),
            ephemeral=True
        )
        
        content = msg.content + " ".join([x.url for x in msg.attachments])
        e = Embed(
            i,
            color=0x2c2f33,
            description="{} **Message reported:** {} ({}) \n\n**Reporter:** {} ({}) \n**Link:** [Here]({})".format(
                self.bot.emotes.get("REPORT"),
                msg.author.mention,
                msg.author.id,
                i.user.mention,
                i.user.id,
                msg.jump_url,
            )
        )
        e.add_fields([
            {
                "name": "Channel",
                "value": f"{msg.channel.mention} ({msg.channel.id})",
                "inline": False
            },
            {
                "name": "Content",
                "value": "```\n{}\n```".format(
                    "None" if len(content) < 1 else content[:1024]
                ),
                "inline": False
            }
        ])
        e.add_view(ActionedView(self.bot, i.user.id))
        await self.log_processor.execute(msg.guild, "report", **{
            "_embed": e
        })

        await i.response.send_message(
            embed=E(self.locale.t(msg.guild, "reported", _emote="YES", user=msg.author), 2), 
            ephemeral=True
        )


async def setup(bot: ShardedBotInstance) -> None: 
    await bot.register_plugin(ModerationPlugin(bot))