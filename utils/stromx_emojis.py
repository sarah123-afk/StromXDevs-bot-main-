"""StromXDevs application emoji support.

The application emojis shown in the supplied Discord Developer Portal screenshots
are identified by their existing emoji names. The bot fetches the application's
emojis at startup, so the project does not need to hard-code emoji snowflake IDs.
"""

from __future__ import annotations

EMOJI_NAMES = ['1000445640', '1000445639', '1000445641', '1000445638', '1000445637', '1000445636', '1000445634', '1000445633', '1000445635', '1000445632', '1000445629', '1000445624', '1000445620', '1000445623', '1000445621', '1000445617', '1000445616', '1000445615', '1000445614', '1000445613', '1000445612', '1000445611', '1000445610', '1000445609', '1000445608', '1000445605', '1000445604', '1000445603', '1000445602', '1000445601', '1000445600', '1000445598', '1000445597', '1000445596', '1000445595', '1000445594', '1000445593', '1000445592', '1000445591', '1000445590', '1000445589', '1000445588', '1000445586', '1000445587', '1000445583', '1000445582', '1000445581', '1000445580', '1000445579', '1000445577', '1000445576', '1000445575', '1000445574', '1000445573', '1000445572', '1000445571', '1000445569', '1000445568', '1000445567', '1000445566', '1000445565', '1000445564', '1000445563', '1000445562', '1000445561', '1000445560', '1000445559', '1000445558', '1000445557', '1000445556', '1000445553', '1000445555', '1000445554', '1000445551', '1000445550', '1000445549', '1000445548', '1000445547', '1000445546', '1000445545', '1000445544', '1000445543', '1000445542', '1000445541', '1000445540', '1000445539', '1000445538', '1000445537', '1000445536', '1000445535', '1000445534', '1000445533', '1000445532', '1000445531', '1000445530', '1000445529', '1000445527', '1000445528', '1000445526', '1000445525', '1000445524', '1000445523', '1000445642', '1000445520', '1000445521', '1000445522', '1000445519', '1000445518', '1000445646', '1000445648', '1000445643', '1000445644', '1000445645', '1000445647', '1000445649', '1000445650', '1000445651', '1000445652', '1000445653']

# Unicode defaults are always available, even when an application emoji cannot be
# fetched or used in a particular server. These are safe Discord-native emoji.
# A command can still pass its own more specific fallback to emoji(name, fallback).
DEFAULT_EMOJI = "✨"
EMOJI_FALLBACKS: dict[str, str] = {
    name: "✨" for name in EMOJI_NAMES
}
EMOJI_FALLBACKS.update({
    "1000445529": "➡️", "1000445528": "⬅️",
    "1000445527": "🎚️", "1000445526": "⏻",
    "1000445525": "⛔", "1000445524": "➕",
    "1000445523": "🗑️", "1000445519": "✅",
    "1000445518": "❌", "1000445540": "🚫",
    "1000445564": "✅", "1000445565": "🔒",
    "1000445573": "➕", "1000445572": "🛡️",
    "1000445571": "⭐", "1000445570": "✨",
})

# Populated after the bot connects. Values are Discord-formatted emoji strings.
_EMOJIS: dict[str, str] = {}


async def load_application_emojis(bot) -> int:
    """Fetch the bot application's emojis and cache the supplied emoji names."""
    _EMOJIS.clear()

    # Application emojis are the primary source. This endpoint is available in
    # recent discord.py releases; if unavailable, native emoji fallbacks still work.
    try:
        fetcher = getattr(bot, "fetch_application_emojis", None)
        application_emojis = await fetcher() if fetcher else []
    except Exception as exc:
        print(f"Could not fetch application emojis: {type(exc).__name__}: {exc}")
        application_emojis = []

    for item in application_emojis:
        name = getattr(item, "name", None)
        if name in EMOJI_NAMES:
            _EMOJIS[name] = str(item)

    # Also accept guild emojis with the same names as a fallback.
    for item in getattr(bot, "emojis", []):
        name = getattr(item, "name", None)
        if name in EMOJI_NAMES:
            _EMOJIS.setdefault(name, str(item))

    print(f"StromXDevs emojis: {len(_EMOJIS)}/{len(EMOJI_NAMES)} custom loaded; native fallbacks enabled")
    return len(_EMOJIS)


def emoji(name: str, fallback: str | None = None) -> str:
    """Return a loaded custom emoji, or a Discord-native fallback if unavailable."""
    key = str(name)
    return _EMOJIS.get(key) or fallback or EMOJI_FALLBACKS.get(key, DEFAULT_EMOJI)


def all_emojis() -> dict[str, str]:
    """Return every screenshot emoji name with custom or native fallback value."""
    return {name: _EMOJIS.get(name, EMOJI_FALLBACKS.get(name, DEFAULT_EMOJI)) for name in EMOJI_NAMES}
