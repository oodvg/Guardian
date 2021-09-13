import logging
import traceback

from .Automod.AutomodPlugin import AutomodPlugin
from .Basic.BasicPlugin import BasicPlugin
from .Admin.AdminPlugin import AdminPlugin
from .Antispam.AntispamPlugin import AntispamPlugin
from .Moderation.ModerationPlugin import ModerationPlugin
from .Error.ErrorPlugin import ErrorPlugin
from .Cases.CasesPlugin import CasesPlugin
from .Config.ConfigPlugin import ConfigPlugin
from .Logs.LogsPlugin import LogsPlugin
from .Persist.PersistPlugin import PersistPlugin
from .Warns.WarnsPlugin import WarnsPlugin
from .Tags.TagsPlugin import TagsPlugin
from .Filters.FiltersPlugin import FiltersPlugin
from .Cache.CachePlugin import CachePlugin
from .Starboard.StarboardPlugin import StarboardPlugin



log = logging.getLogger(__name__)

plugins = {
    # Plugin: Path
    # This also defines the order for the help command
    ErrorPlugin: "src.plugins.Error.ErrorPlugin",

    BasicPlugin: "src.plugins.Basic.BasicPlugin",

    ConfigPlugin: "src.plugins.Config.ConfigPlugin",

    AutomodPlugin: "src.plugins.Automod.AutomodPlugin",

    ModerationPlugin: "src.plugins.Moderation.ModerationPlugin",

    WarnsPlugin: "src.plugins.Warns.WarnsPlugin",

    StarboardPlugin: "src.plugins.Starboard.StarboardPlugin",

    TagsPlugin: "src.plugins.Tags.TagsPlugin",

    AdminPlugin: "src.plugins.Admin.AdminPlugin",

    AntispamPlugin: "src.plugins.Antispam.AntispamPlugin",

    FiltersPlugin: "src.plugins.Filters.FiltersPlugin",

    CasesPlugin: "src.plugins.Cases.CasesPlugin",

    PersistPlugin: "src.plugins.Persist.PersistPlugin",

    LogsPlugin: "src.plugins.Logs.LogsPlugin",

    CachePlugin: "src.plugins.Cache.CachePlugin"
}


async def loadPlugins(bot):
    for plugin, path in plugins.items():
        try:
            plugin.set_path(plugin, path)
            bot.add_cog(plugin(bot))
            bot.load_extension(path)
        except Exception:
            pass
            # ex = traceback.format_exc()
            # log.warn("Failed to load plugin {} - {}".format(plugin, ex))