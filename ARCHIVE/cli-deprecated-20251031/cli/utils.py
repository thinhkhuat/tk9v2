import os
import sys
from typing import Any
from datetime import datetime


class CLIColors:
    """ANSI color codes for terminal output"""
    
    def __init__(self):
        # Check if colors are supported
        self.supports_color = self._supports_color()
        
        if self.supports_color:
            self.RESET = '\033[0m'
            self.BOLD = '\033[1m'
            self.DIM = '\033[2m'
            self.UNDERLINE = '\033[4m'
            
            # Regular colors
            self.BLACK = '\033[30m'
            self.RED = '\033[31m'
            self.GREEN = '\033[32m'
            self.YELLOW = '\033[33m'
            self.BLUE = '\033[34m'
            self.MAGENTA = '\033[35m'
            self.CYAN = '\033[36m'
            self.WHITE = '\033[37m'
            self.GRAY = '\033[90m'
            
            # Bright colors
            self.BRIGHT_RED = '\033[91m'
            self.BRIGHT_GREEN = '\033[92m'
            self.BRIGHT_YELLOW = '\033[93m'
            self.BRIGHT_BLUE = '\033[94m'
            self.BRIGHT_MAGENTA = '\033[95m'
            self.BRIGHT_CYAN = '\033[96m'
            self.BRIGHT_WHITE = '\033[97m'
        else:
            # No color support - set all to empty strings
            for attr in ['RESET', 'BOLD', 'DIM', 'UNDERLINE', 'BLACK', 'RED', 'GREEN', 
                        'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE', 'GRAY',
                        'BRIGHT_RED', 'BRIGHT_GREEN', 'BRIGHT_YELLOW', 'BRIGHT_BLUE',
                        'BRIGHT_MAGENTA', 'BRIGHT_CYAN', 'BRIGHT_WHITE']:
                setattr(self, attr, '')
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output"""
        # Check for common environment variables
        if os.getenv('NO_COLOR'):
            return False
        if os.getenv('FORCE_COLOR'):
            return True
        
        # Check if stdout is a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check TERM environment variable
        term = os.getenv('TERM', '').lower()
        if 'color' in term or term in ['xterm', 'screen', 'tmux']:
            return True
        
        # Check if on Windows and using modern terminal
        if os.name == 'nt':
            return os.getenv('TERM_PROGRAM') in ['vscode', 'WindowsTerminal']
        
        return True


def format_progress(progress: Any) -> str:
    """Format progress information"""
    if isinstance(progress, (int, float)):
        return f"{progress:.1f}%"
    elif isinstance(progress, str):
        return progress
    else:
        return str(progress)


def create_progress_bar(percentage: float, width: int = 40, colors: CLIColors = None) -> str:
    """Create a visual progress bar"""
    if colors is None:
        colors = CLIColors()
    
    # Ensure percentage is between 0 and 100
    percentage = max(0, min(100, percentage))
    
    # Calculate filled and empty portions
    filled_width = int(width * percentage / 100)
    empty_width = width - filled_width
    
    # Create the bar
    filled_bar = '█' * filled_width
    empty_bar = '░' * empty_width
    
    # Format with colors
    bar = f"{colors.GREEN}{filled_bar}{colors.GRAY}{empty_bar}{colors.RESET}"
    
    return f"[{bar}] {percentage:5.1f}%"


def animate_spinner(step: int = 0) -> str:
    """Create spinning animation for progress indication"""
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    return spinners[step % len(spinners)]


class ProgressTracker:
    """Track and display progress for multiple agents"""
    
    def __init__(self, colors: CLIColors = None):
        self.colors = colors or CLIColors()
        self.agents = {}
        self.current_agent = None
        self.start_time = None
        
    def start_agent(self, agent_name: str, description: str = ""):
        """Start tracking progress for an agent"""
        self.agents[agent_name] = {
            'name': agent_name,
            'description': description,
            'progress': 0.0,
            'status': 'running',
            'start_time': datetime.now()
        }
        self.current_agent = agent_name
        
    def update_progress(self, agent_name: str, progress: float, status: str = None):
        """Update progress for an agent"""
        if agent_name in self.agents:
            self.agents[agent_name]['progress'] = progress
            if status:
                self.agents[agent_name]['status'] = status
                
    def complete_agent(self, agent_name: str):
        """Mark an agent as completed"""
        if agent_name in self.agents:
            self.agents[agent_name]['progress'] = 100.0
            self.agents[agent_name]['status'] = 'completed'
            
    def display_summary(self) -> str:
        """Display a summary of all agent progress"""
        if not self.agents:
            return "No agents active"
            
        lines = []
        for agent_name, info in self.agents.items():
            status_color = {
                'running': self.colors.CYAN,
                'completed': self.colors.GREEN,
                'failed': self.colors.RED,
                'waiting': self.colors.YELLOW
            }.get(info['status'], self.colors.RESET)
            
            progress_bar = create_progress_bar(info['progress'], width=20, colors=self.colors)
            status_icon = {
                'running': '▶',
                'completed': '✓',
                'failed': '✗',
                'waiting': '⏸'
            }.get(info['status'], '•')
            
            line = f"{status_color}{status_icon}{self.colors.RESET} {agent_name:<12} {progress_bar}"
            if info['description']:
                line += f" {self.colors.GRAY}({info['description']}){self.colors.RESET}"
            lines.append(line)
            
        return '\n'.join(lines)


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)}m {seconds:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_json_output(data: Any, indent: int = 2) -> str:
    """Format JSON data for console output"""
    import json
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


def print_box(text: str, colors: CLIColors, title: str = None):
    """Print text in a box with optional title"""
    lines = text.split('\n')
    max_width = max(len(line) for line in lines) if lines else 0
    
    if title:
        title_width = len(title) + 2
        box_width = max(max_width, title_width) + 4
    else:
        box_width = max_width + 4
    
    # Top border
    if title:
        print(f"{colors.BLUE}┌─ {title} {'─' * (box_width - len(title) - 4)}┐{colors.RESET}")
    else:
        print(f"{colors.BLUE}┌{'─' * (box_width - 2)}┐{colors.RESET}")
    
    # Content
    for line in lines:
        padding = box_width - len(line) - 4
        print(f"{colors.BLUE}│{colors.RESET} {line}{' ' * padding} {colors.BLUE}│{colors.RESET}")
    
    # Bottom border
    print(f"{colors.BLUE}└{'─' * (box_width - 2)}┘{colors.RESET}")


def print_separator(colors: CLIColors, char: str = "─", length: int = 60):
    """Print a separator line"""
    print(f"{colors.GRAY}{char * length}{colors.RESET}")


def print_status(message: str, status: str, colors: CLIColors):
    """Print a status message with color coding"""
    status_colors = {
        'success': colors.GREEN,
        'error': colors.RED,
        'warning': colors.YELLOW,
        'info': colors.CYAN,
        'progress': colors.BLUE
    }
    
    color = status_colors.get(status.lower(), colors.RESET)
    print(f"{color}[{status.upper()}]{colors.RESET} {message}")


def get_terminal_width() -> int:
    """Get terminal width, defaulting to 80 if not available"""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80