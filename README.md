# team-cac-discord-bot
discord bot written in discord.py just for fun and negative profit

# Purpose
This bot is written to review Python and familiarize myself with SQLite, Poetry, and Discord.py.

In our server there is a Discord user that does not remember to respond to messages that they are mentioned in.

This bot will remind the somewhat unresponsive user that they have unreplied messages that they were mentioned in. It will remind them at specific intervals as specified by the *customer*.

# Technical Decisions

### Python
I just thought decorators were really neat and I read that one *very good* use case for decorators are for writing libraries. It just so happens that Dmany of the Discord Python libraries use decorators so I wanted to see how they worked. I also will likely need Python in the workplace so I figured it just seemed like a good idea.

### Discord.py
I was curious as to how the late, great Discord Python Library was doing so I wanted to check it out. It is being replaced by other libraries that are supposedly better so I wanted to try it before I looked at other libraries such as Hikari.

### SQlite
I just needed persistence with querying capabilities.

### Poetry
I wanted to see what dependency management was like in Python and I wanted something similar to NPM. It seemed better than pip and conda.

# Dependencies:
- `Python 3.9`
- `SQLite 3.37.2`
- `Poetry 1.1.13`
- `Discord.py 1.7.3`

# Infrastructure:
 - Virtual Private Server
    - Digital Ocean Droplet
    - Ubuntu 22.04 Jammy Jellyfish
