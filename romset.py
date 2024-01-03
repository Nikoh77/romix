from typing import IO, Optional, Literal, Any
from logging import Logger
from lxml import etree
import sys

thisLogger: Logger | None

class Romset():
    """
    This class object is a simple timer implementation...
    """
    def __init__(self, descriptor: IO[str], logger: Optional['Logger'] 
                = None) -> None:
        """
        Constructor of the class.

        Arguments:
        - seconds (IO[str]): Romset sidecar file descriptor.
        """
        global thisLogger
        thisLogger = logger
        self.descriptor = descriptor
        if not self.extract_data():
            _tryLogger_(log='Cannot extract data, syntax error parsing xml file',
                        level='critical')
            sys.exit(0)
    
    def extract_data(self) -> bool:
        """
        Extract header data from the XML descriptor using lxml.
        """
        bioses: list[etree._Element] = []
        parents: list[etree._Element] = []
        clones: list[etree._Element] = []
        parser = etree.XMLParser(remove_blank_text=True) # some parser options here
        try:
            tree: etree._ElementTree = etree.parse(source=self.descriptor,
                                                   parser=parser)
            self.header = tree.find(path='//header')
            if self.header is None:
                _tryLogger_(log='No header found', level='warning')
            else:
                header_data: list[str] = ['Working with provided DAT:']
                for i in self.header:
                    header_data.append(f'\n')
                    if i.tag is not None:
                        header_data.append(f'{i.tag}:')
                    if i.text is not None:
                        header_data.append(f' {i.text}')
                    if len(i.attrib) != 0:
                        header_data.append(f' {i.attrib}')
                _tryLogger_(log=''.join(header_data), level='info')
            elements: etree._XPathObject = tree.xpath(_path='//game')
            if isinstance(elements, list):
                for element in elements:
                    if isinstance(element, etree._Element):
                        if element.get(key='isbios') == 'yes':
                            bioses.append(element)
                        else:
                            if element.get(key='cloneof') is None:
                                parents.append(element)
                            else:
                                clones.append(element)
                if len(bioses) > 0:
                    self.bioses = tuple(bioses)
                    _tryLogger_(log=f'Bioses: {len(self.bioses)}',
                                level='info')
                if len(parents) > 0:
                    self.parents = tuple(parents)
                    _tryLogger_(log=f'Parent ROMs: {len(self.parents)}',
                                level='info')
                if len(clones) > 0:
                    self.clones = tuple(clones)
                    _tryLogger_(log=f'Clone ROMs: {len(self.clones)}',
                                level='info')
            else:
                _tryLogger_(log='No game elements found', level='error')
        except Exception as e:
            if isinstance(e, etree.XMLSyntaxError):
                return False
            else:
                raise
        return True
    
    def getData(self, rSet: Literal['bioses', 'parents', 'clones', 'all']
                = 'all') -> dict | None:
        """
        Retrieve specific data elements based on the provided set.

        Args:
            rSet (str): The data set to retrieve. Valid values are 'bioses', 'parents' or
            'clones'; note: nothing = all

        Raises:
            ValueError: If the set or data parameter has an invalid value.

        Return a dict or None:
        {
            "name": {
                "attributes": {
                    "name": str,
                    ...
                },
                "subelements": {
                    "comment": str,
                    "description": str,
                    "year": int | str,
                    "manufacturer": str,
                    "rom": {
                        "name1": {
                            "name": str,
                            "size": int | str,
                            "crc": str
                            ...
                        },
                        "name2": {
                            "name": str,
                            "size": int | str,
                            "crc": str,
                            "sha": str
                            ...
                        },
                        ...
                    },
                    "video": {
                        ...
                    },
                    "driver": {
                        "status": bool
                        ...
                    }
                    ...
                }
            }
        }
        
        Where possible datas are converted to int and bool
        """
        if rSet not in ('bioses', 'parents', 'clones', 'all'):
            raise ValueError(f"Invalid set value: {rSet}")
        if rSet == 'all':
            if hasattr(self, 'parents'):
                temp = self.parents
            if hasattr(self, 'clones'):
                temp = self.parents + self.clones
            if hasattr(self, 'bioses'):
                temp = self.parents + self.clones + self.bioses
        else:
            if hasattr(self, rSet):
                temp = getattr(self, rSet)
        if 'temp' in locals().keys():
            if isinstance(locals()['temp'], tuple) and len(locals()['temp']) > 0:
                reponse: dict = {}
                for element in temp: # type: ignore
                    if element.tag == 'game':
                        game = element.attrib.get('name')
                        reponse.update({game: {'attributes': {}, 'subelements': {}}})
                        for key, value in element.attrib.items():
                            if value is not None:
                                if key == 'isbios':
                                    if value == 'yes':
                                        reponse[game]['attributes'].update({key: True})
                                    else:
                                        reponse[game]['attributes'].update({key: value})
                                else:
                                    reponse[game]['attributes'].update({key: value})
                        for subelement in element:
                            if subelement.tag == 'comment':
                                reponse[game]['subelements'].update({subelement.tag: subelement.text})
                            elif subelement.tag == 'description':
                                reponse[game]['subelements'].update({subelement.tag: subelement.text})
                            elif subelement.tag == 'year':
                                try:
                                    newValue = int(getattr(subelement, 'text'))
                                    reponse[game]['subelements'].update({subelement.tag: newValue})
                                except Exception as e:
                                        _tryLogger_(log=f'Error converting year into integer for {str(object=game)}: {e}')
                                        reponse[game]['subelements'].update({subelement.tag: subelement.text})
                            elif subelement.tag == 'manufacturer':
                                reponse[game]['subelements'].update({subelement.tag: subelement.text})
                            elif subelement.tag == 'rom':
                                rom = subelement.attrib.get('name')
                                if not subelement.tag in reponse[game]['subelements'].keys():
                                    reponse[game]['subelements'].update({subelement.tag: {}})
                                reponse[game]['subelements'][subelement.tag].update({rom: {}})
                                for key, value in subelement.attrib.items():
                                    if value is not None:
                                        if key == 'size':
                                            try:
                                                newValue = int(value)
                                                reponse[game]['subelements'][subelement.tag][rom].update({key: newValue})
                                            except Exception as e:
                                                _tryLogger_(log=f'Error converting year into integer for {str(object=game)}: {e}')
                                                reponse[game]['subelements'][subelement.tag][rom].update({key: value})
                                        else:
                                            reponse[game]['subelements'][subelement.tag][rom].update({key: value})
                            elif subelement.tag == 'video':
                                reponse[game]['subelements'].update({subelement.tag: {}})
                                for key, value in subelement.items():
                                    if value is not None:
                                        if key in {'width', 'height', 'aspectx', 'aspecty'}:
                                            try:
                                                newValue = int(value)
                                                reponse[game]['subelements'][subelement.tag].update({key: newValue})
                                            except Exception as e:
                                                _tryLogger_(log=f'Error converting video data into integer for {str(object=game)}: {e}')
                                                reponse[game]['subelements'][subelement.tag].update({key: value})
                                        else:
                                            reponse[game]['subelements'][subelement.tag].update({key: value})
                            elif subelement.tag == 'driver':
                                reponse[game]['subelements'].update({subelement.tag: {}})
                                for key, value in subelement.items():
                                    if value is not None:
                                        if key == 'status':
                                            if value == 'good':
                                                reponse[game]['subelements'][subelement.tag].update({key: True})
                                            elif value == 'bad':
                                                reponse[game]['subelements'][subelement.tag].update({key: False})
                                            else:
                                                reponse[game]['subelements'][subelement.tag].update({key: value})
                                        else:
                                            reponse[game]['subelements'][subelement.tag].update({key: value})
                            else:
                                reponse[game]['subelements'].update({subelement.tag: subelement.text})
                    else:
                        raise ValueError(f'Non-game element found scanning {rSet}')
                return reponse
            return None
        return None

def _tryLogger_(log: Any, level: Literal['debug', 'info', 'warning', 'error',
                'critical'] = 'debug') -> None:
    if thisLogger is not None:
        thisLogger.name = __name__
        log_method = getattr(thisLogger, level)
        log_method(log)
    else:
        print(f'Error writing log, continuing with simple print\n{log}')