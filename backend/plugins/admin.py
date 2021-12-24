import discord
from discord.ext import commands

import logging; log = logging.getLogger()
import time
import traceback
import ast
import psutil

from . import AutoModPlugin
from ..types import Embed



class AdminPlugin(AutoModPlugin):
    """Plugin for all bot admin commands/events"""
    def __init__(self, bot):
        super().__init__(bot)

    
    def insert_returns(self, body):
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])
        
        if isinstance(body[-1], ast.If):
            self.insert_returns(body[-1].body)
            self.insert_returns(body[-1].orelse)

        if isinstance(body[-1], ast.With):
            self.insert_returns(body[-1].body)


    def parse_shard_info(self, shard: discord.ShardInfo):
        guilds = len(list(filter(lambda x: x.shard_id == shard.id, self.bot.guilds)))
        if not shard.is_closed():
            text = "+ {}: CONNECTED ~ {} guilds".format(shard.id, guilds)
        else:
            text = "- {}: DISCONNECTED ~ {} guilds".format(shard.id, guilds)
        return text


    @commands.command()
    async def eval(self, ctx, *, cmd: str):
        """eval_help"""
        try:
            t1 = time.perf_counter()
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")
            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            body = f"async def {fn_name}():\n{cmd}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            self.insert_returns(body)

            env = {
                "this": ctx,
                "ctx": ctx,
                "db": self.bot.db,
                "bot": self.bot,
                "client": self.bot,
                "discord": discord,
                "commands": commands,
                "__import__": __import__
            }

            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            result = (await eval(f"{fn_name}()", env))
            t2 = time.perf_counter()

            await ctx.message.add_reaction(self.bot.emotes.get("YES"))
            await ctx.send("*Executed in {}ms* \n```py\n{}\n```".format(round((t2 - t1) * 1000, 6), result))
        except Exception:
            ex = traceback.format_exc()
            await ctx.message.add_reaction(self.bot.emotes.get("NO"))
            await ctx.send("```py\n{}\n```".format(ex))



    @commands.command()
    async def debug(self, ctx):
        """debug_help"""
        e = Embed()
        e.add_field(
            name="❯ AutoMod Statistics",
            value="• Last startup: ``{}`` \n• RAM usage: ``{}%`` \n• CPU usage: ``{}%``"\
                .format(
                    self.bot.get_uptime(), 
                    round(psutil.virtual_memory().percent, 2),
                    round(psutil.cpu_percent())
                )
        )
        shards = [self.parseShardInfo(x) for x in self.bot.shards.values()]
        e.add_field(
            name="❯ {} ({})".format(self.bot.user.name, self.bot.user.id),
            value="• Guilds: ``{}`` \n• Latency: ``{}ms`` \n• Total shards: ``{}`` \n• Shard Connectivity: \n```diff\n{}\n```"\
            .format(
                len(self.bot.guilds),
                round(self.bot.latency * 1000, 2), 
                len(self.bot.shards),
                "\n".join(shards)
            )
        )

        await ctx.send(embed=e)


def setup(bot): bot.register_plugin(AdminPlugin(bot))