#!/usr/bin/env python3
"""Deterministic system integration test runner for Treasure Runner."""

import os
import sys
import argparse
from treasure_runner.bindings import Direction
from treasure_runner.models.game_engine import GameEngine
from treasure_runner.models.exceptions import GameError, ImpassableError


def player_state_str(player):
    """Return player state as pipe-separated key=value string."""
    room_id = player.get_room()
    x, y = player.get_position()
    collected = player.get_collected_count()
    return f"room={room_id}|x={x}|y={y}|collected={collected}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Treasure Runner integration test logger"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to generator config file",
    )
    parser.add_argument(
        "--log",
        required=True,
        help="Output log path",
    )
    return parser.parse_args()


def attempt_move(engine, direction):
    """
    Attempt a single move. Returns:
      'moved'    - player position changed in same room
      'treasure' - move succeeded but position unchanged (treasure collected)
      'portal'   - player changed rooms
      'blocked'  - ImpassableError raised
      'error'    - any other exception
    """
    player = engine.player
    before_room = player.get_room()
    before_pos = player.get_position()

    try:
        engine.move_player(direction)
    except ImpassableError:
        return 'blocked'
    except GameError:
        return 'error'
    except Exception:
        return 'error'

    after_room = player.get_room()
    after_pos = player.get_position()

    if after_room != before_room:
        return 'portal'
    if after_pos != before_pos:
        return 'moved'
    return 'treasure'


def safe_reset(engine):
    """Reset engine, ignoring any errors."""
    try:
        engine.reset()
    except Exception:
        pass


def find_entry_direction(engine):
    """
    Find entry direction (SOUTH, WEST, NORTH, EAST).
    Tries each direction, accounting for treasure behaviour.
    """
    order = [Direction.SOUTH, Direction.WEST, Direction.NORTH, Direction.EAST]

    for direction in order:
        for _ in range(20):
            result = attempt_move(engine, direction)
            if result == 'moved':
                safe_reset(engine)
                return direction
            if result == 'treasure':
                continue
            break
        safe_reset(engine)

    return None


def main():
    args = parse_args()
    config_path = os.path.abspath(args.config)
    log_path = os.path.abspath(args.log)

    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    try:
        engine = GameEngine(config_path)
    except Exception as exc:
        print(f"ERROR: Failed to create engine: {exc}", file=sys.stderr)
        return 1

    try:
        with open(log_path, "w", encoding="utf-8") as log:

            log.write(f"RUN_START|config={config_path}\n")

            player = engine.player

            spawn_state = player_state_str(player)
            log.write(f"STATE|step=0|phase=SPAWN|state={spawn_state}\n")

            entry_dir = find_entry_direction(engine)

            if entry_dir is None:
                log.write("ENTRY|dir=NONE\n")
                log.write("TERMINATED: Initial Move Error\n")
                log.write("RUN_END|steps=0|collected_total=0\n")
                return 1

            log.write(f"ENTRY|direction={entry_dir.name}\n")

            step = 0
            entry_done = False

            while not entry_done:
                step += 1
                before_state = player_state_str(player)
                before_collected = player.get_collected_count()

                result = attempt_move(engine, entry_dir)
                after_state = player_state_str(player)

                after_collected = player.get_collected_count()
                delta_collected = after_collected - before_collected

                if result == 'moved' or result == 'portal':
                    log.write(
                        f"MOVE|step={step}|phase=ENTRY|dir={entry_dir.name}"
                        f"|result=OK|before={before_state}|after={after_state}"
                        f"|delta_collected={delta_collected}\n"
                    )
                    entry_done = True

                elif result == 'treasure':
                    log.write(
                        f"MOVE|step={step}|phase=ENTRY|dir={entry_dir.name}"
                        f"|result=OK|before={before_state}|after={after_state}"
                        f"|delta_collected={delta_collected}\n"
                    )

                else:
                    log.write(
                        f"MOVE|step={step}|phase=ENTRY|dir={entry_dir.name}"
                        f"|result=ERROR|before={before_state}|after={after_state}"
                        f"|delta_collected={delta_collected}\n"
                    )
                    log.write("TERMINATED: Initial Move Error\n")
                    collected = player.get_collected_count()
                    log.write(f"RUN_END|steps={step}|collected_total={collected}\n")
                    return 1

            sweep_directions = [
                Direction.SOUTH,
                Direction.WEST,
                Direction.NORTH,
                Direction.EAST,
            ]

            for sweep_dir in sweep_directions:
                phase_name = f"SWEEP_{sweep_dir.name}"
                log.write(f"SWEEP_START|phase={phase_name}|dir={sweep_dir.name}\n")

                seen_states = set()
                seen_states.add(player_state_str(player))
                end_reason = "BLOCKED"

                moves = 0  # Count moves in this sweep

                while True:
                    before_state = player_state_str(player)
                    step += 1

                    before_collected = player.get_collected_count()

                    result = attempt_move(engine, sweep_dir)
                    after_state = player_state_str(player)

                    after_collected = player.get_collected_count()
                    delta_collected = after_collected - before_collected

                    # Only increment moves if actual state change occurred
                    if result in ('moved', 'treasure', 'portal'):
                        moves += 1

                    if result == 'blocked':
                        log.write(
                            f"MOVE|step={step}|phase={phase_name}|dir={sweep_dir.name}"
                            f"|result=BLOCKED|before={before_state}|after={after_state}"
                            f"|delta_collected={delta_collected}\n"
                        )
                        end_reason = "BLOCKED"
                        break

                    if result == 'error':
                        log.write(
                            f"MOVE|step={step}|phase={phase_name}|dir={sweep_dir.name}"
                            f"|result=ERROR|before={before_state}|after={after_state}"
                            f"|delta_collected={delta_collected}\n"
                        )
                        end_reason = "BLOCKED"
                        break

                    if after_state == before_state:
                        log.write(
                            f"MOVE|step={step}|phase={phase_name}|dir={sweep_dir.name}"
                            f"|result=NO_PROGRESS|before={before_state}|after={after_state}"
                            f"|delta_collected={delta_collected}\n"
                        )
                        end_reason = "BLOCKED"
                        break

                    if after_state in seen_states:
                        log.write(
                            f"MOVE|step={step}|phase={phase_name}|dir={sweep_dir.name}"
                            f"|result=OK|before={before_state}|after={after_state}"
                            f"|delta_collected={delta_collected}\n"
                        )
                        end_reason = "CYCLE_DETECTED"
                        break

                    seen_states.add(after_state)
                    log.write(
                        f"MOVE|step={step}|phase={phase_name}|dir={sweep_dir.name}"
                        f"|result=OK|before={before_state}|after={after_state}"
                        f"|delta_collected={delta_collected}\n"
                    )

                log.write(f"SWEEP_END|phase={phase_name}|reason={end_reason}|moves={moves}\n")

            final_state = player_state_str(player)
            log.write(f"STATE|step={step}|phase=FINAL|state={final_state}\n")

            collected_total = player.get_collected_count()
            log.write(f"RUN_END|steps={step}|collected_total={collected_total}\n")

    finally:
        engine.destroy()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())