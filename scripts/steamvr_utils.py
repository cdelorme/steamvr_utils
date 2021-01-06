#!/usr/bin/python3

import argparse
import enum

import log
from audio_switcher import AudioSwitcher
from basestation_interface import BasestationPowerInterface
from config import Config
from steamvr_daemon import SteamvrDaemon


class SteamvrUtils:
    class Action(enum.Enum):
        ON = enum.auto()
        OFF = enum.auto()
        daemon = enum.auto()

    def __init__(self, config):
        self.config = config

        self.streamvr_running = None
        self.turn_off_at = None  # time at which self.turn_of() will be executed (see --wait)

        self.basestation_power_interface = None
        self.audio_switcher = None

        if self.config.basestation_enabled():
            self.basestation_power_interface = BasestationPowerInterface(config)
        if self.config.audio_enabled():
            self.audio_switcher = AudioSwitcher(config)

    def action(self, action):
        if action == self.Action.ON:
            self.turn_on()
        elif action == self.Action.OFF:
            self.turn_off()
        elif action == self.Action.daemon:
            self.start_daemon()
        else:
            raise NotImplementedError('Action: {}'.format(action))

    def start_daemon(self):
        log.i('SteamvrUtils stating daemon:')
        SteamvrDaemon.create_daemon(self)

    def turn_off(self):
        log.i('SteamvrUtils turning off:')

        if self.basestation_power_interface is not None:
            self.basestation_power_interface.robust_action(BasestationPowerInterface.Action.OFF)

        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_normal()

    def turn_on(self):
        log.i('SteamvrUtils turning on:')

        if self.basestation_power_interface is not None:
            self.basestation_power_interface.robust_action(BasestationPowerInterface.Action.ON)

        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_vr()

    def turn_on_iteration(self):
        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_vr()


def main():
    actions = {
        SteamvrUtils.Action.ON: ['on', '1'],
        SteamvrUtils.Action.OFF: ['off', '0'],
        SteamvrUtils.Action.daemon: ['daemon', 'd']
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('action',
                        choices=[
                            keyword
                            for _, keywords in actions.items()
                            for keyword in keywords
                        ],
                        help='action to perform on the Base Stations')
    parser.add_argument('--dry-run',
                        help='Do not modify anything (bluetooth connections are still made, but never used to write).',
                        action='store_true')
    parser.add_argument('--config',
                        default=None,
                        help='Path to a config file.')
    args = parser.parse_args()

    config = Config(config_path=args.config, dry_run_overwrite=args.dry_run)

    log.initialise(config)

    # noinspection PyBroadException
    try:
        log.d('dry_run: {}'.format(config.dry_run()))

        steamvr_utils = SteamvrUtils(
            config=config
        )

        selected_action = None
        for action in SteamvrUtils.Action:
            if args.action in actions[action]:
                selected_action = action

        steamvr_utils.action(selected_action)
    except Exception:
        log.e('', exc_info=True)
        exit(1)


if __name__ == '__main__':
    main()
