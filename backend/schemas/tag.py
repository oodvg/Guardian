from discord.ext import commands

import datetime



def Tag(
    ctx: commands, 
    name: str, 
    content: str,
    del_invoke: bool
) -> dict:
    return {
        "id": f"{ctx.guild.id}-{name}",
        "uses": 0,

        "name": name,
        "content": content,
        "del_invoke": del_invoke,

        "author": f"{ctx.author.id}",
        "editor": None,

        "created": datetime.datetime.utcnow(),
        "edited": None,
    }