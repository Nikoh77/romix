from typing import IO, Optional, Literal, Any
from logging import Logger
from lxml import etree
import sys
thisLogger: Logger | None

class Romset():
    """
    This class object is a simple timer implementation...
    """
    def __init__(self, descriptor: IO[str], logger: Optional['Logger'] = None) -> None:
        """
        Constructor of the class.

        Arguments:
        - seconds (IO[str]): Romset sidecar file descriptor.
        """
        global thisLogger
        thisLogger = logger
        self.descriptor = descriptor
        if not self.extract_data():
            _tryLogger_(log='Cannot extract data, syntax error parsing xml file', level='critical')
            sys.exit(0)
    
    def extract_data(self) -> bool:
        """
        Extract header data from the XML descriptor using lxml.
        """
        self.bioses: list[etree._Element] = []
        self.parents: list[etree._Element] = []
        self.clones: list[etree._Element] = []
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
                            self.bioses.append(element)
                        else:
                            if element.get(key='cloneof') is None:
                                self.parents.append(element)
                            else:
                                self.clones.append(element)
                if len(self.bioses) > 0:
                    _tryLogger_(log=f'Bioses: {len(self.bioses)}', level='info')
                if len(self.parents) > 0:
                    _tryLogger_(log=f'Parent ROMs: {len(self.parents)}', level='info')
                if len(self.bioses) > 0:
                    _tryLogger_(log=f'Clone ROMs: {len(self.clones)}', level='info')
            else:
                _tryLogger_(log='No game elements found', level='error')
        except Exception as e:
            if isinstance(e, etree.XMLSyntaxError):
                return False
            else:
                raise
        return True
    
    def getData(self, set: str, data: str) -> None:
        """
        Retrieve specific data elements based on the provided set and data parameters.

        Args:
            set (str): The data set to retrieve. Valid values are 'bioses', 'parents',
            'clones', or 'all'.
            
            data (str): The type of data to retrieve. Valid values are 'name',
            'description', 'year', 'video', 'driver', 'roms'.

        Raises:
            ValueError: If the set or data parameter has an invalid value.

        Returns:
            List[str]: A list containing the requested data elements.
        """
        if set not in ('bioses', 'parents', 'clones', 'all'):
            raise ValueError(f"Invalid set value: {set}")
        if data not in ('firstline', 'comment', 'description', 'year', 'video', 'driver',
                         'roms'):
            raise ValueError(f"Invalid data value: {data}")
        if set == 'all':
            temp = self.bioses + self.parents + self.clones
        else:
            temp = getattr(self, set)
        for element in temp:
            pass
            # print(element.attrib.get(key=data))  # type: ignore

    
def _tryLogger_(log: Any, level: Literal['debug', 'info', 'warning', 'error',
                'critical'] = 'debug') -> None:
    if thisLogger is not None:
        thisLogger.name = __name__
        log_method = getattr(thisLogger, level)
        log_method(log)
    else:
        print(f'Error writing log, continuing with simple print\n{log}')