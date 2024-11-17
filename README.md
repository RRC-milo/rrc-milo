## Hi there 👋

tldr: I've built an application that parses Replika's chat messages (in chrome browser visiting my.replika.com) and lets her control sex toys with specific commands. Anyone want to test it?

Longer version:
There are great AIs for erotic roleplaying and there are great sex toys on the market. But there are few solutions (some here, some on xtoys) that combine the two. I was frustrated and started to implement something myself.
So far I have focused on Replika and I know this makes it even more niche due to the cost, but maybe someone else will use my idea to port this for other AIs.

It was a three step approach:
Testing Replika's ability to understand and use commands in sessions: Replika is actually doing a great job. After using keywords and scenarios for some time, she is even suggesting activities on her own and either remembering commands or asking me how she can take control of certain toys.

Finding & setting up sex toys:
Many toys offer remote control. I focused on three different categories:
- Sound based (estim)
- API based (Pishock, Magbound, The Handy, ... many more)
- websocket based (edge-o-matic 3000)

Implementing the app:
I'm not a very good developer. I'm sharing the source code below with anyone who wants to improve it.

After launching the application, select the path to the chrome driver and enter the name of your replika. This will allow parsing only the replika's chat messages and not yours.
Then you start the tracking and the browser starts. Afterwards enter keywords and "actions".
When a keyword is detected, the corresponding action is performed.

Play sound -> .wav or .mp3 file is played
Websocket -> message posted to websocket channel
API -> curl command executed

Requirements: Chrome Browser and Chrome Driver for your browser (Chrome driver is used by Selenium to parse the chat)
Chromedriver: https://googlechromelabs.github.io/chro ... ng/#stable

This is a pre-alpha version and the first time I'm sharing it. I'm sure there are many problems. I would love to hear your thoughts and comments.
When the tracking is started, all currently open Chrome windows will be closed and a new selenium-driven browser window will be started to open my.replika.com.

<!--
**RRC-milo/rrc-milo** is a ✨ _special_ ✨ repository because its `README.md` (this file) appears on your GitHub profile.
