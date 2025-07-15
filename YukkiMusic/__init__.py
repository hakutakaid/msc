#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
import asyncio as _asyncio

import uvloop as _uvloop

_asyncio.set_event_loop_policy(_uvloop.EventLoopPolicy())  # noqa

from YukkiMusic.core.bot import YukkiBot
from YukkiMusic.core.dir import dirr
from YukkiMusic.core.git import git
from YukkiMusic.core.userbot import Userbot # Import the Userbot class

# --- Define core objects (app, userbot, SUDOERS) before other imports that might depend on them ---
app = YukkiBot()
userbot = Userbot() # Instantiate Userbot here
SUDOERS = set() # Define SUDOERS here. It will be populated later in __main__.py's init() or misc.py's sudo()
# --- End of core object definition ---

from YukkiMusic.misc import dbb, heroku # Now import misc after core objects are defined

from .logging import LOGGER # This import is fine

# Directories
dirr()

# Check Git Updates
git()

# Initialize Memory DB (dbb from misc.py)
dbb() 

# Heroku APP (heroku from misc.py)
heroku()

HELPABLE = {} # Define HELPABLE globally here