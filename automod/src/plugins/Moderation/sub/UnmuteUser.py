


async def unmuteUser(plugin, ctx, user):
    mute_id = f"{ctx.guild.id}-{user.id}"
    if not plugin.db.mutes.exists(mute_id):
        return await ctx.send(plugin.i18next.t(ctx.guild, "not_muted", _emote="NO"))

    plugin.db.mutes.delete(mute_id)
    await ctx.send(plugin.i18next.t(ctx.guild, "mute_lifted", _emote="YES", user=user))

    # Can we remove the role?
    try:
        mute_role_id = plugin.db.configs.get(ctx.guild.id, "mute_role")
        mute_role = await plugin.bot.utils.getRole(ctx.guild, mute_role_id)
        member = ctx.guild.get_member(user.id)
        await member.remove_roles(mute_role)
    except Exception:
        pass
    finally:
        await plugin.action_logger.log(
            ctx.guild, 
            "manual_unmute", 
            moderator=ctx.message.author, 
            moderator_id=ctx.message.author.id,
            user=user,
            user_id=user.id
        )