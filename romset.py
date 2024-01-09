from typing import IO, Optional, Literal, Any, Union
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
        if not self.__extractData__():
            _tryLogger_(log='Cannot extract data, syntax error parsing xml file',
                        level='critical')
            sys.exit(0)
    
    def __getDocInfo__(self, data: etree.DocInfo) -> bool:
        """
        Extract DOCTYPE data from the XML descriptor using lxml
        and store it in a dictionary named docInfo
        """
        docInfo: dict = {}
        # for prop_name in dir(data):
        for prop_name in data.__dir__():
            if not prop_name.startswith("__"):
                prop_value = getattr(data, prop_name)
                docInfo.update({prop_name: prop_value})
        if len(docInfo) > 0:
            self.docInfo = docInfo
            _tryLogger_(log='Doc info as been retrieved', level='debug')
            return True
        return False

    def __getHeader__(self, data: etree._Element | None) -> bool:
        """
        Extract header data from the XML descriptor using lxml
        and store it in a dictionary named header
        """
        if data is not None:
            if len(data) > 0:
                header_data: dict = {}
                for i in data:
                    header_data.update({i.tag: {}})
                    if i.text is not None:
                        header_data[i.tag]['text'] = i.text
                    if len(i.attrib) != 0:
                        header_data[i.tag]['attributes'] = i.attrib
                if header_data:
                    self.header = header_data
                    _tryLogger_(log='Header as been retrieved', level='debug')
                    return True
        return False
    
    def __extractElements__(self, elements) -> bool:
        """
        Extract games and roms data from the XML descriptor using lxml
        keeping it in etree._Elements
        """
        bioses: list[etree._Element] = []
        parents: list[etree._Element] = []
        clones: list[etree._Element] = []
        try:
            if isinstance(elements, list):
                if len(elements) > 0:
                    for element in elements:
                        if isinstance(element, etree._Element):
                            if element.get(key='isbios') == 'yes':
                                bioses.append(element)
                            else:
                                if 'id' in self.header.keys():
                                    # Working with No-Intro standard dat
                                    if element.get(key='cloneofid') is None:
                                        parents.append(element)
                                    else:
                                        clones.append(element)
                                else:
                                    # Working with Logiqx standard dat
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
                    if ('bioses' or 'parents' or 'clones') in locals().keys():
                        return True
            return False
        except Exception as e:
            _tryLogger_(log='An error occurred retrieving parents, clones and '
                        'bioses')
            return False
    
    def __extractData__(self) -> bool:
        """
        Data extraction manager.
        """
        # Defining game nodeTags, keys are used to scan for some notehead in header and 
        # values are used to scan for game elements
        nodeTags = {
            'no-intro':['game'],
            'finalburn':['game'],
            'mame':['game', 'machine']
        }
        issuers: tuple[str, ...] = ('logiqx', 'no-intro') # Words to search for in doc info
        issuer: str | None = None # If found in the doc info
        hasId: bool = False # If header has ID field
        noteHead: str | None = None # If found in the header
        
        parser = etree.XMLParser(remove_blank_text=True) # some parser options here
        try:
            tree = etree.parse(source=self.descriptor, parser=parser)
            if self.__getDocInfo__(data=tree.docinfo): # retrieving xml DOCInfo
                for info in self.docInfo:
                    if type(self.docInfo[info]) == str:
                        for i in issuers:
                            if i in self.docInfo[info]:
                                issuer = i
                                _tryLogger_(log=f'DOC Type seems like {issuer}'
                                            f' - found in "{info}" DOC Info '
                                            'tag', level='debug')
                                break
                    if issuer != None:
                        break
                if issuer is None:
                        _tryLogger_(log='Unknow xml DOC Type', level='debug')
            else:
                _tryLogger_(log='No xml DOC info found', level='warning')
            # retrieving xml Header
            if not self.__getHeader__(data=tree.find(path='//header')):
                _tryLogger_(log='No header found', level='error')
                return False
            if 'id' in self.header.keys():
                hasId = True # Descriptor has ID
            for element in self.header: # retrieving some "unique" notehead
                for n in nodeTags.keys():
                    if n in self.header[element]['text'].lower():
                        noteHead = n
                        _tryLogger_(log=f'Header seems like {noteHead} - '
                                    f'found in "{element}" header tag')
                        break
                if noteHead != None:
                    break 
            if noteHead is None:
                _tryLogger_(log=f'Descriptor is of unknow type', level='error')
                return False
            schema = getWeight(issuer, hasId, noteHead):
                pass
            # nodeTag = nodeTags.get(schema)
            # if not self.__extractElements__(elements=tree.xpath(_path='//'+f'{nodeTag}')):
            #     _tryLogger_(log=f'No game elements found with tag "{nodeTag}"', level='error')
            #     return False
        except Exception as e:
            if isinstance(e, etree.XMLSyntaxError):
                return False
            else:
                raise
        return True
    
    def getWeight(self, issuer, hasId, noteHead)
    
    def getGames(self, rSet: Literal['bioses', 'parents', 'clones', 'all']
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