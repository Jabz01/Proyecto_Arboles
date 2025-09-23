import json
from pathlib import Path

def load_config(path="config.json"):
    """
    Loads and validates the game configuration file.

    Args:
        path (str): Path to the JSON configuration file.

    Returns:
        tuple: A dictionary containing game parameters ('config'),
               and a list of obstacle definitions ('obstacles').

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If required keys ('config' or 'obstacles') are missing.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"❌ Config file not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "config" not in data or "obstacles" not in data:
        raise KeyError("❌ Config file must contain 'config' and 'obstacles' sections.")

    return data["config"], data["obstacles"]
