#!/usr/bin/env python3

import logging
import platform
import colorlog
import argparse
import os
import json
from typing import Any, Literal
from romset import Romset
from ini import iniSettingsCheck, settings

"""
Defining root variables
"""
supportedOs: list[str] = ['Darwin', 'Windows', 'Linux']
os_name = platform.system()
configFile = 'config.ini'
settingsNeeded = {'test1': ['brand', 'api_key'], 'pixel': ['data1', 'data2']}
foldersNeeded: dict[str, str] = {'screenshots': 'img'}
logLevel = 'debug'
feedFolders: int = 0

logger = colorlog.getLogger(name=__name__)
formatter = colorlog.ColoredFormatter(
    fmt="%(log_color)s[%(levelname)-8s] %(blue)s %(asctime)s %(name)s %(reset)s %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'bold_red',
        'CRITICAL': 'bold_red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)
handler = colorlog.StreamHandler()
handler.setFormatter(fmt=formatter)
logger.addHandler(hdlr=handler)
currentLevel = logging.getLevelName(level=logger.getEffectiveLevel()).lower()
if logLevel != ('' and None and currentLevel):
    getattr(logger, currentLevel)(f'switching from debug level {logging.getLevelName(level=logger.getEffectiveLevel())}')
    logger.setLevel(level=logLevel.upper())
    logger.debug(msg=f'to level {logging.getLevelName(level=logger.getEffectiveLevel())}')

def _tryLogger_(log: Any, level: Literal['debug', 'info', 'warning', 'error',
                'critical'] = 'debug') -> None:
    if logger is not None:
        logger.name = __name__
        log_method = getattr(logger, level)
        log_method(log)
    else:
        print(f'Error writing log, continuing with simple print\n{log}')

def buildSettings(data) -> None:
    for key, value in data.items():
        for sub_key, sub_value in value.items():
            variable_name = f'{key}_{sub_key}'
            variable_name = variable_name.replace(' ', '_')
            variable_name = variable_name.replace('-', '_')
            _tryLogger_(log=f'Assigning global variable {variable_name}'
                            f'from {configFile}', level='debug')
            globals()[variable_name] = sub_value

def foldersFeed(value):
    if not os.path.isdir(s=value):
        raise argparse.ArgumentTypeError(f"{value} is not a directory.")
    global feedFolders
    feedFolders +=1
    _tryLogger_(log=f'Ok, path to {feedFolders} romset folder exist', level='debug')
    # if not os.path.exists(path=value):
    #     raise argparse.ArgumentTypeError(f"{value} does not exist.")
    # _tryLogger_(log='Ok, path to romset descriptor found', level='debug')
    return value

def argparsing() -> Romset | None:
    parser = argparse.ArgumentParser(description='Romix description')
    parser.add_argument('-d', '--dat', metavar='file',
                        type=argparse.FileType(mode='r'),
                        required=True,
                        help='path to romset descriptor')
    parser.add_argument('-r', '--romset', metavar='folder',
                        type=foldersFeed, help='Path to romset folder')
    parser.add_argument('-f', '--feed', metavar='folder',
                        nargs='+', # feed can take more than one path
                        type=foldersFeed, help='Path to feeding folder')
    try:
        args = parser.parse_args()
        _tryLogger_(log='Ok, romset descriptor found', level='debug')
        with open(file=args.dat.name, mode="r", encoding="utf-8") as file:
            romset = Romset(descriptor=file, logger=logger)
            _tryLogger_(log='Ok, descriptor parsing has been completed successfully', level='debug' )
            if args.romset:
                scanner(romset=romset, arguments=args)
    except SystemExit as e:
        if e.code == 2:
            _tryLogger_(log="Unrecognized or unprovided arguments.", level='critical')
            # TODO Gestione dell'eccezione facendo qualcosa oppure cancellare la
            # gestione e lasciarlo gestire da argparser
        else:
            raise  # Raise exception if different from SystemExit
    return None

def scanner(romset: Romset, arguments: argparse.Namespace):
    print(arguments)
    
    # fileNumber = os.listdir(arguments.romset)
    data = romset.getData(set='bioses')
    filesList = data.keys()
    all_files = []
    for root, dirs, files in os.walk(top=arguments.romset):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            all_files.append(file_path)
    print(all_files)

        

def main() -> None:
    if os_name not in supportedOs:
        _tryLogger_(log=f'{os_name} usupported OS', level='critical')
        return
    _tryLogger_(log=f'{os_name} detected, continuing with supported OS...', level='debug')
    if not iniSettingsCheck(options=settingsNeeded, config_file=configFile,
            folders=foldersNeeded, logger=logger):
        _tryLogger_(log=f'An error as occured initialising settings', level='critical')
        return
    buildSettings(data=settings)
    romset = argparsing()

if __name__ == '__main__':
    main()
    _tryLogger_(log='Romix terminated', level='info')