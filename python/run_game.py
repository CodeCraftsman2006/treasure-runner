"""
run_game.py – entry point for Treasure Run A3.

Usage:
    python3 run_game.py --config <path/to/config.ini> --profile <path/to/profile.json>

--config  : path to the world .ini file
--profile : path to the player profile JSON file
            (created automatically if it does not exist)
"""

import argparse
import curses
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# making sure the treasure_runner package can be found even if we run from diff directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from treasure_runner.models.game_engine import GameEngine
from treasure_runner.ui.game_ui import GameUI, TerminalTooSmallError, prompt_player_name


# default profile values if user doesnt have one yet
DEFAULT_PROFILE = {
    "player_name": "Player",
    "games_played": 0,
    "max_treasure_collected": 0,
    "most_rooms_world_completed": 0,
    "timestamp_last_played": "",
}


def load_or_create_profile(profile_path: str) -> dict:
    """
    Load the JSON profile at profile_path.

    If the file does not exist:
      - prompt the user for a player name via curses
      - create a default profile at that path
      - return the new profile dict

    Returns the profile as a plain Python dict.
    """
    path = Path(profile_path)  # convert string path to Path object

    if path.exists():
        # if file already exists just load it and return
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # if profile doesnt exist we ask user for their name using curses UI
    name = curses.wrapper(prompt_player_name)

    # create a new profile based on default values
    profile = dict(DEFAULT_PROFILE)
    profile["player_name"] = name or "Player"  # fallback if nothing entered
    profile["timestamp_last_played"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # store time in UTC format
    )

    # make sure directory exists before writing file
    path.parent.mkdir(parents=True, exist_ok=True)

    # write the new profile to file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    return profile  # return the created profile


def parse_args() -> argparse.Namespace:
    # setting up argument parser for command line inputs
    parser = argparse.ArgumentParser(
        prog="run_game.py",
        description="Treasure Run – A3",
    )
    parser.add_argument(
        "--config",
        required=True,
        metavar="PATH",
        help="Path to the world configuration .ini file",  # config file for game world
    )
    parser.add_argument(
        "--profile",
        required=True,
        metavar="PATH",
        help="Path to the player profile JSON file",  # where user stats are stored
    )
    return parser.parse_args()  # parse and return arguments


def main() -> None:
    args = parse_args()  # get command line args

    # load existing profile or create new one if missing
    profile = load_or_create_profile(args.profile)

    # create game engine with config file
    engine = GameEngine(args.config)
    try:
        # create UI and run the game loop
        ui = GameUI(engine, profile, args.profile)
        ui.run()
    except TerminalTooSmallError as exc:
        # handles case where terminal window is too small for UI
        print(f"Error: {exc}", file=sys.stderr)
        #sys.exit(1)
    finally:
        # always destroy engine to free resources (important)
        engine.destroy()


if __name__ == "__main__":
    # entry point of program
    main()