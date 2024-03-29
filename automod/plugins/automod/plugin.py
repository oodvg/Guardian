# type: ignore

import discord
from discord.ext import commands

import re
from ...__obj__ import TypeHintedToolboxObject as Object
from urllib.parse import urlparse
from typing import TypeVar, Literal, Optional, List
import logging; log = logging.getLogger()
from typing import Union, Tuple, Dict

from .. import AutoModPluginBlueprint, ShardedBotInstance
from .._processor import ActionProcessor, LogProcessor, DMProcessor
from ...types import Embed, E
from ...views import RoleChannelSelect
from ...modals import AutomodRuleModal



INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord(?:\.| |\[?\(?\"?'?dot'?\"?\)?\]?)?(?:gg|io|me|li)|discord(?:app)?\.com/invite)/+((?:(?!https?)[\w\d-])+)"
)


LINK_RE = re.compile(
    r"((?:https?://)[a-z0-9]+(?:[-._][a-z0-9]+)*\.[a-z]{2,5}(?::[0-9]{1,5})?(?:/[^ \n<>]*)?)", 
    re.IGNORECASE
)


MENTION_RE = re.compile(
    r"<@[!&]?\\d+>"
)


EMOTE_RE = re.compile(
    r"<(a?):([^: \n]+):([0-9]{15,20})>"
)


ALLOWED_FILE_FORMATS = [
    # plain text/markdown
    "txt",
    "md",

    # image
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",

    # video
    "mov",
    "mp4",
    "flv",
    "mkv",

    # audio
    "mp3",
    "wav",
    "m4a"
]


ZALGO = [
    u'\u030d',
    u'\u030e',
    u'\u0304',
    u'\u0305',
    u'\u033f',
    u'\u0311',
    u'\u0306',
    u'\u0310',
    u'\u0352',
    u'\u0357',
    u'\u0351',
    u'\u0307',
    u'\u0308',
    u'\u030a',
    u'\u0342',
    u'\u0343',
    u'\u0344',
    u'\u034a',
    u'\u034b',
    u'\u034c',
    u'\u0303',
    u'\u0302',
    u'\u030c',
    u'\u0350',
    u'\u0300',
    u'\u030b',
    u'\u030f',
    u'\u0312',
    u'\u0313',
    u'\u0314',
    u'\u033d',
    u'\u0309',
    u'\u0363',
    u'\u0364',
    u'\u0365',
    u'\u0366',
    u'\u0367',
    u'\u0368',
    u'\u0369',
    u'\u036a',
    u'\u036b',
    u'\u036c',
    u'\u036d',
    u'\u036e',
    u'\u036f',
    u'\u033e',
    u'\u035b',
    u'\u0346',
    u'\u031a',
    u'\u0315',
    u'\u031b',
    u'\u0340',
    u'\u0341',
    u'\u0358',
    u'\u0321',
    u'\u0322',
    u'\u0327',
    u'\u0328',
    u'\u0334',
    u'\u0335',
    u'\u0336',
    u'\u034f',
    u'\u035c',
    u'\u035d',
    u'\u035e',
    u'\u035f',
    u'\u0360',
    u'\u0362',
    u'\u0338',
    u'\u0337',
    u'\u0361',
    u'\u0489',
    u'\u0316',
    u'\u0317',
    u'\u0318',
    u'\u0319',
    u'\u031c',
    u'\u031d',
    u'\u031e',
    u'\u031f',
    u'\u0320',
    u'\u0324',
    u'\u0325',
    u'\u0326',
    u'\u0329',
    u'\u032a',
    u'\u032b',
    u'\u032c',
    u'\u032d',
    u'\u032e',
    u'\u032f',
    u'\u0330',
    u'\u0331',
    u'\u0332',
    u'\u0333',
    u'\u0339',
    u'\u033a',
    u'\u033b',
    u'\u033c',
    u'\u0345',
    u'\u0347',
    u'\u0348',
    u'\u0349',
    u'\u034d',
    u'\u034e',
    u'\u0353',
    u'\u0354',
    u'\u0355',
    u'\u0356',
    u'\u0359',
    u'\u035a',
    u'\u0323',
]


ZALGO_RE = re.compile(
    u"|".join(ZALGO)
)


LOG_DATA = {
    "invites": {
        "rule": "Invite Filter"
    },
    "links": {
        "rule": "Link Filter"
    },
    "links_blacklist": {
        "rule": "Link Filter (blacklist)"
    },
    "files": {
        "rule": "Attachment Filter"
    },
    "zalgo": {
        "rule": "Zalgo Filter"
    },
    "lines": {
        "rule": "Line Filter"
    },
    "length": {
        "rule": "Length Filter"
    },
    "mentions": {
        "rule": "Mentions Filter"
    },
    "emotes": {
        "rule": "Emotes Filter"
    },
    "repeat": {
        "rule": "Repetition Filter"  
    },
    "regex": {
        "rule": "Regex Filter"
    },
    "filter": {
        "rule": "Word Filter"
    },
    "antispam": {
        "rule": "Spam Filter"
    },
    "caps": {
        "rule": "CAPS Filter"
    }
}


AUTOMOD_RULES = {
    "mentions": {
        "int_field_name": "threshold",
        "i18n_key": "set_mentions",
        "i18n_type": "maximum mentions",
        "field_name": "mention",
        "field_help": "mentions"
    },
    "links": {
        "int_field_name": "warns",
        "i18n_key": "set_links",
        "i18n_type": "link filtering",
        "field_name": "warn",
        "field_help": "warns"
    },
    "invites": {
        "int_field_name": "warns",
        "i18n_key": "set_invites",
        "i18n_type": "invite filtering",
        "field_name": "warn",
        "field_help": "warns"
    },
    "files": {
        "int_field_name": "warns",
        "i18n_key": "set_files",
        "i18n_type": "bad file detection",
        "field_name": "warn",
        "field_help": "warns"
    },
    "lines": {
        "int_field_name": "threshold",
        "i18n_key": "set_lines",
        "i18n_type": "maximum lines",
        "field_name": "line",
        "field_help": "lines"
    },
    "length": {
        "int_field_name": "threshold",
        "i18n_key": "set_length",
        "i18n_type": "maximum characters",
        "field_name": "character",
        "field_help": "characters"
    },
    "emotes": {
        "int_field_name": "threshold",
        "i18n_key": "set_emotes",
        "i18n_type": "maximum emotes",
        "field_name": "emote",
        "field_help": "emotes"
    },
    "repeat": {
        "int_field_name": "threshold",
        "i18n_key": "set_repeat",
        "i18n_type": "maximum repetitions",
        "field_name": "repeat",
        "field_help": "repeat"
    },
    "zalgo": {
        "int_field_name": "warns",
        "i18n_key": "set_zalgo",
        "i18n_type": "zalgo filtering",
        "field_name": "warn",
        "field_help": "warns"
    },
    "caps": {
        "int_field_name": "warns",
        "i18n_key": "set_caps",
        "i18n_type": "CAPS filtering",
        "field_name": "warn",
        "field_help": "warns"
    }
}


BYPASS_TO_SECONDS = {
    "1 Month": 2678400,
    "3 Months": 8035200,
    "6 Moths": 16070400,
    "1 Year": 32140800
}


ILLEGAL_CHARS = [
    "­", # soft hyphen
    "​", # zero width space
    "\\"
]


CHANNEL_OR_ROLE_T = TypeVar("CHANNEL_OR_ROLE_T", discord.Role, discord.TextChannel)


class AutomodPlugin(AutoModPluginBlueprint):
    """Plugin for enforcing automoderator rules"""
    def __init__(self, bot: ShardedBotInstance) -> None:
        super().__init__(bot)
        self.action_processor = ActionProcessor(bot)
        self.log_processor = LogProcessor(bot)
        self.dm_processor = DMProcessor(bot)
        self.spam_cache: Dict[int, commands.CooldownMapping] = {}
        self.recent_messages: Dict[int, Dict[int, List[discord.Message]]] = {}


    def update_recent_messages(self, msg: discord.Message) -> None:
        if not msg.author.id in self.recent_messages:
            self.recent_messages[msg.guild.id] = [msg]
        else:
            last_ten = self.recent_messages[msg.author.id].get(msg.guild.id, [])
            if len(last_ten) == 10:
                last_ten[-1] = msg
            else:
                last_ten.append(msg)
            
            self.recent_messages[msg.author.id].update({
                msg.guild.id: last_ten
            })
    

    def get_recent_messages(self, msg: discord.Message) -> List[Optional[discord.Message]]:
        if not msg.author.id in self.recent_messages:
            return []
        else:
            return self.recent_messages[msg.author.id].get(msg.guild.id, [])


    def can_act(self, guild: discord.Guild, mod: discord.Member, target: Union[discord.Member, discord.User]) -> bool:
        if mod.id == target.id: return False
        if mod.id == guild.owner_id: return True

        mod = guild.get_member(mod.id)
        target = guild.get_member(target.id)
        if mod == None or target == None: return False

        rid = self.bot.db.configs.get(guild.id, "mod_role")
        if rid != "" and rid != None:
            if int(rid) in [x.id for x in target.roles]: return False

        return mod.id != target.id \
            and target.id != guild.owner.id \
            and (
                target.guild_permissions.ban_members == False 
                or target.guild_permissions.kick_members == False 
                or target.guild_permissions.manage_messages == False
            )
    

    def can_ignore(self, guild: discord.Guild, channel: discord.TextChannel, target: Union[discord.Member, discord.User]) -> bool:
        roles, channels = self.get_ignored_roles_channels(guild)
        if channels == None:
            self.db.configs.update(guild.id, "ignored_channels_automod", [])
        else:
            if channel.id in channels: return True

        if any(x in [i.id for i in target.roles] for x in roles): return True
        return False


    def parse_filter(self, words: List[str]) -> Optional[re.Pattern]:
        normal = []
        wildcards = []

        for i in words:
            i = i.replace("*", "", (i.count("*") - 1)) # remove multiple wildcards
            if i.endswith("*"):
                wildcards.append(re.escape(i.replace("*", ".+")))
            else:
                normal.append(re.escape(i))

        try:
            return re.compile(r"|".join([*normal, *wildcards]), re.IGNORECASE)
        except Exception:
            return None


    def parse_regex(self, regex: str) -> Optional[re.Pattern]:
        try:
            parsed = re.compile(regex, re.IGNORECASE)
        except Exception:
            return None
        else:
            return parsed


    def validate_regex(self, regex: str) -> bool:
        try:
            re.compile(regex)
        except re.error:
            return False
        else:
            return True


    def safe_parse_url(self, url: str) -> str:
        url = url.lower()
        if not (
            url.startswith("https://") or
            url.startswith("http://")
        ):
            for x in [
                "www", 
                "www5", 
                "www2", 
                "www3"
            ]:
                url = url.replace(x, "")
        else:
            url = urlparse(url).hostname
        return url


    def parse_channels(self, channels: str) -> List[int]:
        final = []
        for s in channels.split(", "):
            if s.isdigit():
                final.append(int(s))
        return final


    def get_ignored_roles_channels(self, guild: discord.Guild) -> Tuple[List[str], List[str]]:
        roles, channels = self.db.configs.get(guild.id, "ignored_roles_automod"), self.db.configs.get(guild.id, "ignored_channels_automod")
        return roles, channels


    def sanitize_content(self, content: str) -> str:
        for c in ILLEGAL_CHARS:
            content = content.replace(c, "")
        return content
    

    def replace_vars(self, msg: discord.Message, inp: str, rule: str) -> str:
        vars = {
            "{user}": f"{msg.author.mention}",
            "{username}": f"{msg.author.display_name}",
            "{channel}": f"{msg.channel.mention}",
            "{server}": f"{msg.guild.name}",
            "{rule}": rule.title()
        }

        for k, v in vars.items():
            inp = inp.replace(k, v)
        return inp
    

    async def send_response(self, msg: discord.Message, rule: str) -> None:
        cfg = self.db.configs.get(msg.guild.id, "automod")
        if rule.lower() in cfg:
            response: Optional[str] = cfg[rule].get("response", None)
            if response != None and response != "":
                try:
                    await msg.channel.send(content=self.replace_vars(msg, response, rule))
                except Exception:
                    pass

    
    def get_automod_reason(self, rule: Object, default: str) -> str:
        if hasattr(rule, "reason"):
            if rule.reason != None: 
                return rule.reason
            else:
                return default
        else:
            return default

        
    async def delete_msg(self, rule: str, found: str, msg: discord.Message, warns: int, reason: str, pattern_or_filter: Optional[str] = None) -> None:
        try:
            await msg.delete()
        except (
            discord.NotFound, 
            discord.Forbidden
        ):
            pass
        else:
            self.bot.ignore_for_events.append(msg.id)
        finally:
            await self.send_response(msg, rule) 
            data = Object(LOG_DATA[rule])

            if warns > 0:
                await self.action_processor.execute(
                    msg, 
                    msg.guild.me,
                    msg.author,
                    warns, 
                    reason,
                    **{
                        "rule": data.rule if rule not in ["filter", "regex"] else None,
                        "pattern": f"{pattern_or_filter}",
                        "found": found,
                        "channel_id": msg.channel.id,
                        "content": msg.content,
                    }
                )
            else:
                self.dm_processor.execute(
                    msg,
                    "automod_rule_triggered",
                    msg.author,
                    **{
                        "guild_name": msg.guild.name,
                        "rule": data.rule,
                        "_emote": "SWORDS"
                    }
                )
                if rule not in ["filter", "regex"]:
                    await self.log_processor.execute(
                        msg.guild,
                        "automod_rule_triggered",
                        **{
                            "rule": data.rule,
                            "found": found,
                            "user_id": msg.author.id,
                            "user": msg.author,
                            "mod": msg.guild.me,
                            "mod_id": msg.guild.me.id,
                            "channel_id": msg.channel.id,
                            "content": msg.content,
                            "case": self.action_processor.new_case("automod", msg, msg.guild.me, msg.author, f"{reason}, automated by AutoMod")
                        }
                    )
                else:
                    await self.log_processor.execute(
                        msg.guild,
                        f"{rule}_triggered",
                        **{
                            "pattern": f"{pattern_or_filter}",
                            "found": found,
                            "user_id": msg.author.id,
                            "user": msg.author,
                            "mod": msg.guild.me,
                            "mod_id": msg.guild.me.id,
                            "channel_id": msg.channel.id,
                            "content": msg.content,
                            "case": self.action_processor.new_case(rule, msg, msg.guild.me, msg.author, f"{reason}, automated by AutoMod")
                        }
                    )


    async def execute_punishment(self, rule: str, found: str, msg: discord.Message, warns: int, reason: str, pattern_or_filter: Optional[str] = None) -> None:
        pass


    async def enforce_rules(self, msg: discord.Message) -> None:
        content = self.sanitize_content(msg.content)

        config = Object(self.db.configs.get_doc(msg.guild.id))
        rules = config.automod
        filters = config.filters
        regexes = config.regexes
        antispam = config.antispam

        if antispam.enabled == True:
            if not self.can_ignore(msg.guild, msg.channel, msg.author):
                if not msg.guild.id in self.spam_cache:
                    self.spam_cache.update({
                        msg.guild.id: commands.CooldownMapping.from_cooldown(
                            antispam.rate,
                            float(antispam.per),
                            commands.BucketType.user
                        )
                    })
                
                mapping = self.spam_cache[msg.guild.id]
                now = msg.created_at.timestamp()

                users = mapping.get_bucket(msg)
                if users.update_rate_limit(now):
                    to_delete = self.get_recent_messages(msg)
                    if len(to_delete) > 0:
                        try:
                            await msg.channel.delete_messages(to_delete)
                        except Exception:
                            pass

                    return await self.delete_msg(
                        "antispam",
                        f"**``{users.rate}/{round(users.per, 0)}``**",
                        msg, 
                        antispam.warns, 
                        "Spam detected"
                    )
                else:
                    self.update_recent_messages(msg)


        if len(filters) > 0:
            for name in filters:
                f = filters[name]
                if msg.channel.id in f["channels"] or len(f["channels"]) < 1:
                    parsed = self.parse_filter(f["words"])
                    if parsed != None:
                        found = parsed.findall(content)
                        if found:
                            return await self.delete_msg(
                                "filter",
                                ", ".join([f"**``{x}``**" for x in found]),
                                msg, 
                                int(f["warns"]), 
                                "Blacklisted spam",
                                name
                            )
        
        if len(regexes) > 0:
            for name, data in regexes.items():
                if msg.channel.id in data["channels"] or len(data["channels"]) < 1:
                    parsed = self.parse_regex(data["regex"])
                    if parsed != None:
                        found = parsed.findall(content)
                        if found:
                            return await self.delete_msg(
                                "regex",
                                ", ".join([f"**``{x}``**" for x in found]),
                                msg, 
                                int(data["warns"]), 
                                "Blacklisted spam",
                                name
                            )
        
        if len(rules) < 1: return
        if self.can_ignore(
            msg.guild, 
            msg.channel, 
            msg.author
        ): return

        if hasattr(rules, "invites"):
            found = INVITE_RE.findall(content)
            if found:
                for inv in found:
                    try:
                        invite: discord.Invite = await self.bot.fetch_invite(inv)
                    except discord.NotFound:
                        return await self.delete_msg(
                            "invites",
                            f"**``{inv}``**",
                            msg, 
                            rules.invites.warns, 
                            self.get_automod_reason(
                                rules.invites, 
                                "Sending Discord invite link or equivalent redirect"
                            )
                        )
                    if invite.guild == None:
                        return await self.delete_msg(
                            "invites",
                            f"**``{inv}``**",
                            msg, 
                            rules.invites.warns, 
                            self.get_automod_reason(
                                rules.invites, 
                                "Sending Discord invite link or equivalent redirect"
                            )
                        )
                    else:
                        if invite.guild == None \
                            or (
                                not invite.guild.id in config.allowed_invites \
                                and invite.guild.id != msg.guild.id
                            ):
                                return await self.delete_msg(
                                    "invites",
                                    f"**``{inv}``**",
                                    msg, 
                                    rules.invites.warns, 
                                    self.get_automod_reason(
                                        rules.invites, 
                                        "Sending Discord invite link or equivalent redirect"
                                    )
                                )
        
        if hasattr(rules, "links"):
            found = LINK_RE.findall(content)
            if found:
                for link in found:
                    url = urlparse(link)
                    if url.hostname in config.black_listed_links:
                        return await self.delete_msg(
                            "links_blacklist", 
                            f"**``{url.hostname}``**",
                            msg, 
                            rules.links.warns, 
                            self.get_automod_reason(
                                rules.links, 
                                "Posting a link without permission"
                            )
                        )
                    else:
                        if not url.hostname in config.white_listed_links:
                            return await self.delete_msg(
                                "links", 
                                f"**``{url.hostname}``**",
                                msg, 
                                rules.links.warns, 
                                self.get_automod_reason(
                                    rules.links, 
                                    "Posting a link without permission"
                                )
                            )

        if hasattr(rules, "files"):
            if len(msg.attachments) > 0:
                try:
                    forbidden = [
                        x.url.split(".")[-1] for x in msg.attachments \
                        if not x.url.split(".")[-1].lower() in ALLOWED_FILE_FORMATS
                    ]
                except Exception:
                    forbidden = []
                if len(forbidden) > 0:
                    return await self.delete_msg(
                        "files", 
                        ", ".join([f"**``{x}``**" for x in forbidden]), 
                        msg, 
                        rules.files.warns, 
                        self.get_automod_reason(
                            rules.files, 
                            "Posting forbidden attachment type"
                        )
                    )

        if hasattr(rules, "zalgo"):
            found = ZALGO_RE.search(content)
            if found:
                return await self.delete_msg(
                    "zalgo", 
                    f"``{found.group()}``", 
                    msg, 
                    rules.zalgo.warns, 
                    self.get_automod_reason(
                        rules.zalgo, 
                        "Excessive or/and unwanted use of symbols"
                    )
                )

        if hasattr(rules, "mentions"):
            found = len(MENTION_RE.findall(content))
            if found > rules.mentions.threshold:
                return await self.delete_msg(
                    "mentions", 
                    f"**``{found}``**", 
                    msg, 
                    0 if (found - rules.mentions.threshold) == 1 else 1, 
                    self.get_automod_reason(
                        rules.mentions, 
                        "Excessive use of mentions"
                    )
                )

        if hasattr(rules, "lines"):
            found = len(content.split("\n"))
            if found > rules.lines.threshold:
                return await self.delete_msg(
                    "lines", 
                    f"**``{found}``**", 
                    msg, 
                    0 if (found - rules.lines.threshold) == 1 else 1, 
                    self.get_automod_reason(
                        rules.lines, 
                        "Message too long"
                    )
                )
            
        if hasattr(rules, "length"):
            if len(content) > rules.length.threshold:
                return await self.delete_msg(
                    "length", 
                    f"**``{found}``**", 
                    msg, 
                    0 if (found - rules.length.threshold) == 1 else 1, 
                    self.get_automod_reason(
                        rules.length, 
                        "Message too long"
                    )
                )

        if hasattr(rules, "emotes"):
            found = len(EMOTE_RE.findall(content))
            if found > rules.emotes.threshold:
                return await self.delete_msg(
                    "emotes", 
                    f"**``{found}``**", 
                    msg, 
                    0 if (found - rules.emotes.threshold) == 1 else 1, 
                    self.get_automod_reason(
                        rules.emotes, 
                        "Excessive use of emotes"
                    )
                )

        if hasattr(rules, "repeat"):
            found = {}
            for word in content.split(" "):
                found.update({
                    word.lower(): found.get(word.lower(), 0) + 1
                })
            if len(found.keys()) < 12:
                for k, v in found.items():
                    if v > rules.repeat.threshold:
                        return await self.delete_msg(
                            "repeat", 
                            f"**``{k} ({v}x)``**", 
                            msg, 
                            0 if (v - rules.repeat.threshold) == 1 else 1, 
                            self.get_automod_reason(
                                rules.repeat, 
                                "Duplicated text"
                            )
                        )
        
        if hasattr(rules, "caps"):
            if len(content) > 10:
                perc_caps = round(((len([x for x in content if x.isupper()]) / len(content)) * 100))
                if perc_caps >= 75:
                    return await self.delete_msg(
                        "caps", 
                        f"**``{perc_caps}% in {len(content)} chars``**", 
                        msg, 
                        rules.caps.warns, 
                        self.get_automod_reason(
                            rules.caps, 
                            "Excessive use of CAPS"
                        )
                    )


    @AutoModPluginBlueprint.listener()
    async def on_message(self, msg: discord.Message) -> None:
        if msg.guild == None: return
        if not msg.guild.chunked: await self.bot.chunk_guild(msg.guild)
        if not self.can_act(msg.guild, msg.guild.me, msg.author): return

        await self.enforce_rules(msg)


    @AutoModPluginBlueprint.listener()
    async def on_message_edit(self, _, msg: discord.Message) -> None:
        if msg.guild == None: return
        if not msg.guild.chunked: await self.bot.chunk_guild(msg.guild)
        if not self.can_act(msg.guild, msg.guild.me, msg.author): return

        await self.enforce_rules(msg)


    @AutoModPluginBlueprint.listener()
    async def on_interaction(self, i: discord.Interaction) -> None:
        cid = i.data.get("custom_id", "").lower()
        parts = cid.split(":")

        if len(parts) != 2: return
        if not "automod" in parts[0]: return
        
        if parts[1] == "channels":
            func = i.guild.get_channel
        else:
            func = i.guild.get_role

        inp = [func(int(r)) for r in i.data.get("values", [])]
        roles, channels = self.get_ignored_roles_channels(i.guild)
        added, removed, ignored = [], [], []
        
        if parts[0] == "automod_add":
            for e in inp:
                if isinstance(e, discord.Role):
                    if not e.id in roles:
                        roles.append(e.id); added.append(e)
                    else:
                        ignored.append(e)
                elif isinstance(e, (discord.TextChannel, discord.ForumChannel)):
                    if not e.id in channels:
                        channels.append(e.id); added.append(e)
                    else:
                        ignored.append(e)
        else:
            for e in inp:
                if isinstance(e, discord.Role):
                    if e.id in roles:
                        roles.remove(e.id); removed.append(e)
                    else:
                        ignored.append(e)
                elif isinstance(e, (discord.TextChannel, discord.ForumChannel)):
                    if e.id in channels:
                        channels.remove(e.id); removed.append(e)
                    else:
                        ignored.append(e)
                else:
                    ignored.append(e)
        
        self.db.configs.multi_update(i.guild.id, {
            "ignored_roles_automod": roles,
            "ignored_channels_automod": channels
        })
        if parts[0] != "automod_add": added = removed

        e = Embed(
            i,
            title="Updated the following roles & channels"
        )
        e.add_fields([
            {
                "name": "Roles",
                "value": "{}".format(", ".join(
                    [
                        x.mention for x in added if isinstance(x, discord.Role)
                    ]
                )) if len(
                    [
                        _ for _ in added if isinstance(_, discord.Role)
                    ]
                ) > 0 else f"{self.bot.emotes.get('NO')}"
            },
            {
                "name": "Channels",
                "value": "{}".format(", ".join(
                    [
                        x.mention for x in added if isinstance(x, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
                    ]
                )) if len(
                    [
                        _ for _ in added if isinstance(_, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))
                    ]
                ) > 0 else f"{self.bot.emotes.get('NO')}"
            },
            {
                "name": "Ignored",
                "value": "{}".format(", ".join(
                    [
                        x.mention for x in ignored if x != None
                    ]
                )) if len(
                    [
                        _ for _ in ignored if _ != None
                    ]
                ) > 0 else f"{self.bot.emotes.get('NO')}"
            },
        ])

        await i.response.edit_message(embed=e)

    
    automod_command = discord.app_commands.Group(
        name="automod", 
        description="🔰 Configure the automoderator (use /setup for more info)",
        default_permissions=discord.Permissions(manage_guild=True)
    )
    @automod_command.command(
        name="enable",
        description="🔰 Enable/edit an automod rule"
    )
    @discord.app_commands.describe(
        rule="The rule you want to enable/edit"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def automod_enable(
        self, 
        ctx: discord.Interaction, 
        rule: Literal[
            "Invites filter", 
            "Links filter", 
            "Attachments filter", 
            "Mentions filter", 
            "Line filter",
            "Length filter", 
            "Emotes filter", 
            "Repetition filter", 
            "Zalgo filter", 
            "Caps filter"
        ],
    ) -> None:
        """
        automod_enable_help
        examples:
        -automod enable Invites filter
        -automod enable Mentions filter
        -automod enable Links filter
        """  
        rule = {
            "invites filter": "invites", 
            "links filter": "links", 
            "attachments filter": "files", 
            "mentions filter": "mentions", 
            "line filter": "lines", 
            "length filter": "length",
            "emotes filter": "emotes", 
            "repetition filter": "repeat", 
            "zalgo filter": "zalgo", 
            "caps filter": "caps"
        }.get(rule.lower())
        current = self.db.configs.get(ctx.guild.id, "automod")
        data = Object(AUTOMOD_RULES[rule])

        async def callback(i: discord.Interaction) -> None:
            amount, response, reason, _ = self.bot.extract_args(i, "amount", "response", "reason", "vars")

            try:
                amount = int(amount)
            except Exception:
                return await i.response.send_message(embed=E(self.locale.t(i.guild, "num_req", _emote="NO", arg="amount"), 0), ephemeral=True)

            if rule in ["mentions", "lines", "emotes", "repeat"]:
                if amount < 5: return await i.response.send_message(embed=E(self.locale.t(i.guild, "min_am_amount", _emote="NO", field=rule.replace("s", "")), 0), ephemeral=True)
                if amount > 100: return await i.response.send_message(embed=E(self.locale.t(i.guild, "max_am_amount", _emote="NO", field=rule.replace("s", "")), 0), ephemeral=True)
            else:
                if rule == "length":
                    if amount < 20: return await i.response.send_message(embed=E(self.locale.t(i.guild, "min_chars", _emote="NO"), 0), ephemeral=True)
                    if amount > 4000: return await i.response.send_message(embed=E(self.locale.t(i.guild, "max_chars", _emote="NO"), 0), ephemeral=True)
                else:
                    if amount < 0: return await i.response.send_message(embed=E(self.locale.t(i.guild, "min_warns_esp", _emote="NO"), 0), ephemeral=True)
                    if amount > 100: return await i.response.send_message(embed=E(self.locale.t(i.guild, "max_warns", _emote="NO"), 0), ephemeral=True)

            current.update({
                rule: {
                    data.int_field_name: int(amount),
                    "response": response if response != "" else None,
                    "reason": reason if reason != "" else None
                }
            })
            self.db.configs.update(i.guild.id, "automod", current)

            text = ""
            if not rule in ["mentions", "lines", "length", "emotes", "repeat"] and amount == 0:
                if rule == "links":
                    text = self.locale.t(i.guild, f"{data.i18n_key}_zero", _emote="YES", cmd=f"</links add:{self.bot.internal_cmd_store.get('links')}>")
                elif rule == "invites":
                    text = self.locale.t(i.guild, f"{data.i18n_key}_zero", _emote="YES", cmd=f"</links add:{self.bot.internal_cmd_store.get('links')}>")
                else:
                    text = self.locale.t(i.guild, f"{data.i18n_key}_zero", _emote="YES")
            else:
                if rule == "links":
                    text = self.locale.t(i.guild, data.i18n_key, _emote="YES", amount=amount, plural="" if amount == 1 else "s", cmd=f"</links add:{self.bot.internal_cmd_store.get('links')}>")
                elif rule == "invites":
                    text = self.locale.t(i.guild, data.i18n_key, _emote="YES", amount=amount, plural="" if amount == 1 else "s", cmd=f"</invites add:{self.bot.internal_cmd_store.get('invites')}>")
                else:
                    text = self.locale.t(i.guild, data.i18n_key, _emote="YES", amount=amount, plural="" if amount == 1 else "s")
            await i.response.send_message(embed=E(text, 1))

        modal = AutomodRuleModal(
            self.bot, 
            f"Configure {rule.title()} Rule", 
            "threshold" if rule in ["mentions", "lines", "emotes", "repeat", "length"] else "warns",
            current.get(rule, {}).get(data.int_field_name, None),
            current.get(rule, {}).get("response", None),
            current.get(rule, {}).get("reason", None),
            callback
        )
        await ctx.response.send_modal(modal)

    
    @automod_command.command(
        name="disable",
        description="🔰 Disable an automod rule"
    )
    @discord.app_commands.describe(
        rule="The rule you want to disable"
    )
    async def automod_disable(
        self, 
        ctx: discord.Interaction, 
        rule: Literal[
            "Invites filter", 
            "Links filter", 
            "Attachments filter", 
            "Mentions filter", 
            "Line filter",
            "Length filter", 
            "Emotes filter", 
            "Repetition filter", 
            "Zalgo filter", 
            "Caps filter"
        ],
    ) -> None:
        """
        automod_disable_help
        examples:
        -automod disable Invites filter
        -automod disable Mentions filter
        -automod disable Links filter
        """  
        rule = {
            "invites filter": "invites", 
            "links filter": "links", 
            "attachments filter": "files", 
            "mentions filter": "mentions", 
            "line filter": "lines", 
            "length filter": "length", 
            "emotes filter": "emotes", 
            "repetition filter": "repeat", 
            "zalgo filter": "zalgo", 
            "caps filter": "caps"
        }.get(rule.lower())
        current = self.db.configs.get(ctx.guild.id, "automod")
        data = Object(AUTOMOD_RULES[rule])

        if rule not in current:
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_automod_off", _emote="NO", _type=data.i18n_type.title()), 0))
        else:
            self.db.configs.update(ctx.guild.id, "automod", {k: v for k, v in current.items() if k != rule})
            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "automod_off", _emote="YES", _type=data.i18n_type.title()), 1))


    allowed_invites = discord.app_commands.Group(
        name="invites",
        description="🔀 Configure allowed invite links",
        default_permissions=discord.Permissions(manage_guild=True)
    )
    @allowed_invites.command(
        name="list",
        description="🔗 Shows all currently allowed invite links"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def show_inv(self, ctx: discord.Interaction,) -> None:
        """
        allowed_invites_help
        examples:
        -allowed_invites list
        """
        allowed = [f"``{x.strip().lower()}``" for x in self.db.configs.get(ctx.guild.id, "allowed_invites")]
        if len(allowed) < 1: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "no_allowed", _emote="NO", prefix="/"), 0), ephemeral=True)
        
        e = Embed(
            ctx,
            title="Allowed invites (by server ID)",
            description="{}".format(", ".join(allowed))
        )
        await ctx.response.send_message(embed=e)


    @allowed_invites.command(
        name="add",
        description="✅ Adds a guild to the allowed invite list"
    )
    @discord.app_commands.describe(
        guild_id="The ID of the server you want to whitelist"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def add_inv(self, ctx: discord.Interaction, guild_id: str) -> None:
        """
        allowed_invites_add_help
        examples:
        -allowed_invites add 701507539589660793
        """
        allowed = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "allowed_invites")]
        if str(guild_id) in allowed: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_allowed", _emote="NO"), 0), ephemeral=True)
        
        allowed.append(str(guild_id))
        self.db.configs.update(ctx.guild.id, "allowed_invites", allowed)

        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "allowed_inv", _emote="YES"), 1))


    @allowed_invites.command(
        name="remove",
        description="❌ Removes a guild from the allowed invite list"
    )
    @discord.app_commands.describe(
        guild_id="The ID of the server you want to remove from the whitelist"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def remove_inv(self, ctx: discord.Interaction, guild_id: str) -> None:
        """
        allowed_invites_remove_help
        examples:
        -allowed_invites remove 701507539589660793
        """
        allowed = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "allowed_invites")]
        if not str(guild_id) in allowed: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_allowed", _emote="NO"), 0), ephemeral=True)
        
        allowed.remove(str(guild_id))
        self.db.configs.update(ctx.guild.id, "allowed_invites", allowed)

        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "unallowed_inv", _emote="YES"), 1))


    _links = discord.app_commands.Group(
        name="links",
        description="🔀 Configure the link blacklist & whitelist",
        default_permissions=discord.Permissions(manage_guild=True)
    )
    @_links.command(
        name="list",
        description="🔗 Shows the current link blacklist or whitelist"
    )
    @discord.app_commands.describe(
        type="What list type to check"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def show_link(self, ctx: discord.Interaction,type: Literal["Blacklist", "Whitelist"]) -> None:
        """
        link_blacklist_help
        examples:
        -links list Blacklist
        """
        if type.lower() == "blacklist":
            links = [f"``{x.strip().lower()}``" for x in self.db.configs.get(ctx.guild.id, "black_listed_links")]
            if len(links) < 1: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "no_links", _emote="NO", prefix="/"), 0), ephemeral=True)
            
            e = Embed(
                ctx,
                title="Blacklisted links",
                description="{}".format(", ".join(links))
            )
            await ctx.response.send_message(embed=e)
        else:
            links = [f"``{x.strip().lower()}``" for x in self.db.configs.get(ctx.guild.id, "white_listed_links")]
            if len(links) < 1: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "no_links2", _emote="NO", prefix="/"), 0), ephemeral=True)
            
            e = Embed(
                ctx,
                title="Allowed links",
                description="{}".format(", ".join(links))
            )
            await ctx.response.send_message(embed=e)


    @_links.command(
        name="add",
        description="✅ Adds a link to the blacklist or whitelist"
    )
    @discord.app_commands.describe(
        type="The type of list this link is for",
        url="The URl to add to the list (e.g. google.com)"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def add_link(self, ctx: discord.Interaction, type: Literal["Blacklist", "Whitelist"], url: str) -> None:
        """
        link_blacklist_add_help
        examples:
        -links add Blacklist google.com
        """
        url = self.safe_parse_url(url)
        if type.lower() == "blacklist":
            links = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "black_listed_links")]
            if str(url) in links: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_link", _emote="NO"), 0), ephemeral=True)
            
            links.append(url)
            self.db.configs.update(ctx.guild.id, "black_listed_links", links)

            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "allowed_link", _emote="YES"), 1))
        else:
            links = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "white_listed_links")]
            if str(url) in links: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "alr_link2", _emote="NO"), 0), ephemeral=True)
            
            links.append(url)
            self.db.configs.update(ctx.guild.id, "white_listed_links", links)

            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "allowed_link2", _emote="YES"), 1))


    @_links.command(
        name="remove",
        description="❌ Removes the link from the blacklist or whitelist"
    )
    @discord.app_commands.describe(
        type="The type of list this link is for",
        url="The URl to remove from the list (e.g. google.com)"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def remove_link(self, ctx: discord.Interaction, type: Literal["Blacklist", "Whitelist"], url: str) -> None:
        """
        link_blacklist_remove_help
        examples:
        -links remove Blacklist google.com
        """
        url = self.safe_parse_url(url)
        if type.lower() == "blacklist":
            links = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "black_listed_links")]
            if not str(url) in links: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_link", _emote="NO"), 0), ephemeral=True)
            
            links.remove(url)
            self.db.configs.update(ctx.guild.id, "black_listed_links", links)

            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "unallowed_link", _emote="YES"), 1))
        else:
            links = [x.strip().lower() for x in self.db.configs.get(ctx.guild.id, "white_listed_links")]
            if not str(url) in links: return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "not_link2", _emote="NO"), 0), ephemeral=True)
            
            links.remove(url)
            self.db.configs.update(ctx.guild.id, "white_listed_links", links)

            await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "unallowed_link2", _emote="YES"), 1))


    antispam_command = discord.app_commands.Group(
        name="antispam",
        description="🔄 Configure the spam filter",
        default_permissions=discord.Permissions(manage_guild=True)
    )
    @antispam_command.command(
        name="enable",
        description="🔄 Enable the spam filter"
    )
    @discord.app_commands.describe(
        rate="Allowed amount of messages",
        per="Timeframe the amount messages are allowed to be sent in",
        warns="Amount of warns users should receive when spam is detected"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def antispam(
        self, 
        ctx: discord.Interaction, 
        rate: discord.app_commands.Range[int, 3, 21], 
        per: discord.app_commands.Range[int, 3, 20], 
        warns: discord.app_commands.Range[int, 1, 100]
    ) -> None:
        """
        antispam_help
        examples:
        -antispam
        -antispam 12 10 3
        """
        config = self.db.configs.get(ctx.guild.id, "antispam")
        config.update({
            "enabled": True,
            "rate": rate,
            "per": per,
            "warns": warns
        })

        am_plugin = self.bot.get_plugin("AutomodPlugin")
        am_plugin.spam_cache.update({
            ctx.guild.id: commands.CooldownMapping.from_cooldown(
                rate,
                float(per),
                commands.BucketType.user
            )
        })
        self.db.configs.update(ctx.guild.id, "antispam", config)
        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "enabled_antispam", _emote="YES", rate=rate, per=per, warns=warns), 1))


    @antispam_command.command(
        name="disable",
        description="🔄 Disable the spam filter"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def antispam(
        self, 
        ctx: discord.Interaction
    ) -> None:
        """
        antispam_help
        examples:
        -antispam disable
        """
        config = self.db.configs.get(ctx.guild.id, "antispam")
        if config["enabled"] == False:
            return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "antispam_alr_disabled", _emote="NO"), 0), ephemeral=True)

        config.update({
            "enabled": False
        })
        self.db.configs.update(ctx.guild.id, "antispam", config)
        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "disabled_antispam", _emote="YES"), 1))


    ignore_automod = discord.app_commands.Group(
        name="ignore-automod",
        description="🔀 Manage ignored roles & channels for the automoderator",
        default_permissions=discord.Permissions(manage_guild=True)
    )
    @ignore_automod.command(
        name="list",
        description="🔒 Shows the current list of ignored roles & channels for the automoderator"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def show(self, ctx: discord.Interaction) -> None:
        """
        ignore_automod_help
        examples:
        -ignore-automod list
        """
        roles, channels = self.get_ignored_roles_channels(ctx.guild)

        if (len(roles) + len(channels)) < 1:
            return await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "no_ignored_am", _emote="NO"), 0), ephemeral=True)
        else:
            e = Embed(
                ctx,
                title="Ignored roles & channels for the automoderator"
            )
            e.add_fields([
                {
                    "name": "Roles",
                    "value": "{}".format(", ".join([f"<@&{x}>" for x in roles])) if len(roles) > 0 else "> None"
                },
                {
                    "name": "Channels",
                    "value": "{}".format(", ".join([f"<#{x}>" for x in channels])) if len(channels) > 0 else "> None"
                }
            ])

            await ctx.response.send_message(embed=e)


    @ignore_automod.command(
        name="add",
        description="✅ Adds the given role or channel as ignored for the automoderator"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def add(self, ctx: discord.Interaction) -> None:
        """
        ignore_automod_add_help
        examples:
        -ignore-automod add
        """
        view = RoleChannelSelect("automod_add")
        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "bypass_add"), color=2), view=view, ephemeral=True)


    @ignore_automod.command(
        name="remove",
        description="❌ Removes the given role or channel as ignored for the automoderator"
    )
    @discord.app_commands.default_permissions(manage_guild=True)
    async def remove(self, ctx: discord.Interaction) -> None:
        """
        ignore_automod_remove_help
        examples:
        -ignore-automod remove
        """
        view = RoleChannelSelect("automod_remove")
        await ctx.response.send_message(embed=E(self.locale.t(ctx.guild, "bypass_remove"), color=2), view=view, ephemeral=True)


async def setup(bot: ShardedBotInstance) -> None: 
    await bot.register_plugin(AutomodPlugin(bot))