


async def run(plugin, ctx):
    prefix = plugin.db.configs.get(ctx.guild.id, "prefix")
    await ctx.send(plugin.i18next.t(ctx.guild, "filter_cmd_help", _emote="WARN", prefix=prefix))