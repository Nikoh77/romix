# This module is needed by the main and takes care of the control and generation of the
# configuration file through input requests.

import configparser
import os
from logging import Logger
from typing import Any, Literal

settings: dict[Any, Any] = {}
thisLogger: Logger | None

def iniSettingsCheck(options, config_file, folders, logger) -> bool:
    config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'), comment_prefixes=('#', ';'),
                                       empty_lines_in_values=False, allow_no_value=False)
    config.read(filenames=config_file)
    global thisLogger
    thisLogger = logger
    for section in options:
        if not config.has_section(section=section):
            _tryLogger_(log=f'Needed section {section} does not exist in your INI '
                        f'file, creating...', level='info')
            config.add_section(section=section)
        for option in options[section]:
            if config.has_option(section=section, option=option):
                _tryLogger_(log=f'Ok, {section} {option} found.', level='info')
            else:
                config.set(
                    section=section,
                    option=option,
                    value=input(f'Please insert the {section} {option}: ')
                )
    with open(file=config_file, mode='w') as configfile:
        config.write(fp=configfile)
    # Read INI file
    for section in config.sections():
        options = config.items(section=section)
        data = {}
        for option, value in options:
            if value != ('' and None):
                data[option] = value
            settings[section] = data
    if settings:
        if iniStructCheck(folders=folders):
            _tryLogger_(log=f'Ok, all folders are in place', level='info')
            return True
    return False

def iniStructCheck(folders) -> bool:
    for folder in folders:
        if not os.path.exists(path=folders.get(folder)):
            os.makedirs(name=folders.get(folder))
    return True

def _tryLogger_(log: Any, level: Literal['debug', 'info', 'warning', 'error',
                'critical'] = 'debug') -> None:
    if thisLogger is not None:
        thisLogger.name = __name__
        log_method = getattr(thisLogger, level)
        log_method(log)
    else:
        print(f'Error writing log, continuing with simple print\n{log}')
