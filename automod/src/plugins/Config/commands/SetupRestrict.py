from discord import PermissionOverwrite

from ..sub.Overwrites import overwrite

from ....utils.Views import ConfirmView



async def run(plugin, ctx):
    message = None
    async def cancel(interaction):
        await interaction.response.edit_message(content=plugin.i18next.t(ctx.guild, "aborting"), view=None)

    async def timeout():
        if message is not None:
            await message.edit(content=plugin.i18next.t(ctx.guild, "aborting"), view=None)

    def check(interaction):
        return interaction.user.id == ctx.author.id and interaction.message.id == message.id

    async def confirm(interaction):
        await interaction.response.edit_message(content=plugin.i18next.t(ctx.guild, "start_restrict", _emote="YES"), view=None)
        msg = interaction.message


        global embed_role
        embed_role_id = plugin.db.configs.get(ctx.guild.id, "embed_role")
        if embed_role_id != "":
            embed_role = await plugin.bot.utils.getRole(ctx.guild, int(embed_role_id))
        else:
            try:
                embed_role = await ctx.guild.create_role(name="Embed restricted")
            except Exception as ex:
                return await msg.edit(content=plugin.i18next.t(ctx.guild, "role_fail2", _emote="NO", role="Embed restricted", exc=ex))


        global emoji_role
        emoji_role_id = plugin.db.configs.get(ctx.guild.id, "emoji_role")
        if emoji_role_id != "":
            emoji_role = await plugin.bot.utils.getRole(ctx.guild, int(emoji_role_id))
        else:
            try:
                emoji_role = await ctx.guild.create_role(name="Emoji restricted")
            except Exception as ex:
                return await msg.edit(content=plugin.i18next.t(ctx.guild, "role_fail2", _emote="NO", role="Emoji restricted", exc=ex))


        global tag_role
        tag_role_id = plugin.db.configs.get(ctx.guild.id, "tag_role")
        if tag_role_id != "":
            tag_role = await plugin.bot.utils.getRole(ctx.guild, int(tag_role_id))
        else:
            try:
                tag_role = await ctx.guild.create_role(name="Tag restricted")
            except Exception as ex:
                return await msg.edit(content=plugin.i18next.t(ctx.guild, "role_fail2", _emote="NO", role="Tag restricted", exc=ex))
            else:
                plugin.db.configs.update(ctx.guild.id, "tag_role", f"{tag_role.id}")


        await msg.edit(content=f"{msg.content} \n{plugin.emotes.get('YES')} Roles initialized!")
        await overwrite(
            plugin, 
            ctx, 
            msg, 
            {
                "embed_role": {"role": embed_role, "perms": PermissionOverwrite(embed_links=False)}, 
                "emoji_role": {"role": emoji_role, "perms": PermissionOverwrite(external_emojis=False)}
            }
        )

    message = await ctx.send(
        "This will create (or edit) 3 roles (Embed restricted, Emoji restricted & Tag restricted)",
        view=ConfirmView(
            ctx.guild.id, 
            on_confirm=confirm, 
            on_cancel=cancel, 
            on_timeout=timeout,
            check=check
        )
    )