# Reel Lab

You film your clips. Claude edits the reel.

This is the plugin for buyers of Reel Lab. The walkthrough videos and support are in your portal: https://portal.tenfoldmarketing.com

## Install in the Claude desktop app

1. Open the Claude desktop app and go to the **Code** tab.
2. Click the **+** next to the message box, then **Plugins**, then **Browse plugins**.
3. Click **Add** in the top right, then **Add marketplace**, then **Add from a repository**.
4. Paste this link and click **Sync**:

```
https://github.com/vladsdigital/reel-lab
```

5. Install **Reel Lab** from the list.
6. Start a new chat and type:

```
/reel-lab setup
```

Setup asks where your clips land, then builds your editing style with you: send links to reels whose editing you love (or describe it, or pick from the Studio's built-in looks), and name it. It downloads its tools in the background while you do that. Your first edit dials the style in, and after that you just drop clips in and say: edit these in [your style].

## Install from a terminal instead

Only if you use Claude Code in Terminal (Mac) or PowerShell (Windows). Run these yourself, not inside Claude. Each line is one paste.

```bash
claude plugin marketplace add vladsdigital/reel-lab
```

```bash
claude plugin install reel-lab@reel-lab
```

On Windows this route needs [Git for Windows](https://git-scm.com/downloads) installed first.

Then open Claude Code and type `/reel-lab setup`.

## Carousels

The Studio makes carousels too, in your own look. In any chat, say:

```
make a carousel about [your topic]
```

or

```
turn my last reel into a carousel
```

The first time, it asks for your handle and your look: send screenshots of carousels you love and it rebuilds that style, or pick one of the 3 looks it comes with. Then it writes the copy for every slide, waits for your OK, designs the slides and opens a preview you can swipe through like the real post. The slides land in a Carousels folder in your home folder, ready to post.

## Getting updates

Fixes and new effects arrive as updates to this plugin. Your picks and your own style are kept.

**The easy way:** when there is a new version, Claude tells you and asks if you want it. Say yes. You can also say this at any time:

```
update the Studio
```

**From a terminal instead:** each line is one paste.

```bash
claude plugin marketplace update reel-lab
```

```bash
claude plugin update reel-lab@reel-lab
```

Start a new chat after an update so Claude loads the new version.

## Help

Email info@tenfoldmarketing.com. Say what you were doing and what happened. A screenshot helps.

---

© Ten Fold Marketing. For buyers of Reel Lab, under the terms you agreed to at purchase. Not affiliated with or endorsed by Anthropic or Instagram.
