embed
<drac2>
args = &ARGS&
ch = character()

# Optional thumbnail from active character
thumb = f' -thumb "{ch.image}"' if ch.image else ''

# ------------------------------------------------------------
# Help mode only when explicitly requested
# ------------------------------------------------------------
if args and args[0].lower() in ["help", "?"]:
    desc = "\n".join([
        "**Usage (message must be quoted)**",
        "- `!send \"message...\"`",
        "- `!send -t <target> \"message...\"`",
        "- `!send -b ...` (block if over 25 words instead of truncating)",
        "",
        "**Examples**",
        "- `!send \"Meet at dusk.\"`",
        "- `!send -t Rowan \"Meet at dusk.\"`",
        "- `!send -b \"This message is too long ...\"`",
        "",
        "**Notes**",
        "- Sending is limited to **25 words**.",
        "- Messages over 25 words are **truncated** by default.",
        "- Use `-b` to **block** instead.",
        "- Target is displayed as plain text (no ping)."
    ]).replace('"', "'")
    return f'-title "Sending Help" -desc "{desc}"{thumb}'

block = False
target = None

# ------------------------------------------------------------
# Parse flags: -b and -t <target>
# Remaining args must resolve to exactly ONE quoted message
# ------------------------------------------------------------
i = 0
parts = []

while i < len(args):
    a = args[i]

    if a == "-b":
        block = True
        i += 1
        continue

    if a == "-t" and (i + 1) < len(args):
        target = args[i + 1]
        i += 2
        continue

    parts.append(a)
    i += 1

# Enforce quoted message
if len(parts) != 1:
    desc = "\n".join([
        "Message text must be enclosed in quotes.",
        "",
        "**Usage**",
        "- `!send \"message...\"`",
        "- `!send -t <target> \"message...\"`",
        "- `!send -b \"message...\"`",
        "",
        "**Examples**",
        "- `!send \"Hello world\"`",
        "- `!send -t Rowan \"Meet at dusk\"`",
        "- `!send -b \"This is a long message ...\"`",
        "",
        "Use `!send help` for details."
    ]).replace('"', "'")
    return f'-title "Sending" -desc "{desc}"{thumb}'

message = parts[0].strip()
words = message.split()
count = len(words)

if count == 0:
    return f'-title "Sending" -desc "No message provided. Use `!send help` for usage."{thumb}'

# ------------------------------------------------------------
# Enforce 25-word limit
# Default: truncate. Optional: block with -b.
# ------------------------------------------------------------
if count > 25 and block:
    desc = "\n".join([
        "A faint chime echoes through the Weave.",
        "Your message exceeded the capacity of this sending.",
        "Please shorten your thoughts and try again."
    ]).replace('"', "'")

    out = []
    out.append('-title "Sending Failed"')
    out.append(f'-desc "{desc}"')
    out.append(f'-f "Word Count|{count} (limit 25)"')
    out.append(thumb)
    return " ".join(out)

# Truncate if needed (default behavior)
truncated = False
if count > 25:
    message = " ".join(words[:25]) + "..."
    truncated = True

# ------------------------------------------------------------
# Build success embed
# ------------------------------------------------------------
desc = f'"{message}"'.replace('"', "'")
title = f'{ch.name} sends a message'

out = []
out.append(f'-title "{title}"')
out.append(f'-desc "{desc}"')
out.append(thumb)

if target:
    out.append(f'-f "To|{target}"')

if truncated:
    out.append('-f "Note|The message seems to continue, but the rest is lost."')

return " ".join(out)
</drac2>

-footer "!send ? | @konnivingkrook#0"
