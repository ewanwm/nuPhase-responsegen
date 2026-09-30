"""
Creates a NReWeight instance that can be used to apply reweights to the currenly loaded event
"""
from __future__ import annotations
import typing
__all__: list[str] = ['NReWeight', 'NeutReader', 'initialise', 'make_reweight_instance']
class NReWeight:
    """
    Handles reweighting. Should be accessed via the make_reweight_instance() function
    
    Usage would look something like
    
    .. code:: python
    
        initialise(<card file>)
        reader = NeutReader(<neut file>)
        reader.get_entry(0)
    
        ## this is the NReWeight instance
        reweighter = make_reweight_instance()
    
        for dial_name in <list of dial names>:
    
            ## check that the dial is actually handled by some reweight engine
            assert reweighter.dial_is_handled(dial_name)
    
            for value in <list of dial values>:
    
                ## set the dial to some value
                reweighter.set_dial(dial, value)
    
                ## registers any changes to dials
                reweighter.reconfigure()
    
                weight = reweighter.calc_weight()
    
                print(weight)
    
                ## resets any changes to dials
                reweighter.reset()
    
    .. note:: The call to reconfigure() *before* calc_weight() and the call to reset() *after*
    
    """
    def __init__(self) -> None:
        ...
    def calc_weight(self) -> float:
        """
        Calculate a weight for the current event given all currently configured dial values
        """
    def dial_is_handled(self, dial_name: str) -> bool:
        """
        Check if a dial is handled by one of NEUTs reweighting engines
        """
    def get_dial_generated(self, dial_name: str) -> float:
        """
        Get the value of the dial that was used to generate the current neut file
        """
    def get_dial_sigma(self, dial_name: str) -> float:
        """
        Get the NEUT one sigma uncertainty for a dial
        """
    def reconfigure(self) -> None:
        """
        Registers any dial values that have been set. Should be called after all calls to set_dial_value() and before call to calc_weight()
        """
    def reset(self) -> None:
        """
        Reset dial values. You will probably want to call this after calc_weight() and before setting any new dial values
        """
    def set_dial(self, dial_name: str, dial_value: typing.SupportsFloat | typing.SupportsIndex) -> None:
        """
        Set a dial to some value
        """
class NeutReader:
    """
    Simple helper class to aid in reading events from a neut file
    
    Neut uses global variables when reading events so any event loaded by this class becomes *THE* current neut event
    
    .. warning::
        
        You should only ever have one NeutReader 'active' at a given time
    
    """
    def __init__(self, input_file_name: str) -> None:
        ...
    def get_entries(self) -> int:
        """
        Get the number of entries in the file
        """
    def get_entry(self, arg0: typing.SupportsInt | typing.SupportsIndex) -> bool:
        """
        Read a particular entry for the file - this will alter the global neut state to load the specified 'event' as the current one
        """
def initialise(card_file: str) -> None:
    """
    Initialises NEUT related global things. This *must* be called before doing anything else Neut related
    """
def make_reweight_instance() -> NReWeight:
    ...
