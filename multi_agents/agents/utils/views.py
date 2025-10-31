from colorama import Fore, Style
from enum import Enum


class AgentColor(Enum):
    RESEARCHER = Fore.LIGHTBLUE_EX
    EDITOR = Fore.YELLOW
    WRITER = Fore.LIGHTGREEN_EX
    PUBLISHER = Fore.MAGENTA
    REVIEWER = Fore.CYAN
    REVISOR = Fore.LIGHTWHITE_EX
    MASTER = Fore.LIGHTYELLOW_EX
    PROVIDERS = Fore.GREEN
    ERROR = Fore.RED
    ORCHESTRATOR = Fore.LIGHTCYAN_EX
    ORCHESTRATOR_SETUP = Fore.LIGHTCYAN_EX
    DEBUG = Fore.LIGHTMAGENTA_EX
    LANGUAGE = Fore.LIGHTBLUE_EX


def print_agent_output(output:str, agent: str="RESEARCHER"):
    try:
        color = AgentColor[agent].value
    except KeyError:
        # Default color if agent not found in enum
        color = Fore.WHITE
    print(f"{color}{agent}: {output}{Style.RESET_ALL}")