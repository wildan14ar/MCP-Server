"""
Server Tools Registration for FastMCP
Registers all server tools to MCP server
"""

from mcp.server.fastmcp import FastMCP
from . import server


def register_server_tools(mcp: FastMCP):
    """
    Register all server MCP tools.
    
    Categories:
    - Basic Info: whoami, pwd, hostname, uname
    - File Listing: ls, tree
    - File Search: find_files, grep_files, locate_file
    - File Operations: cat_file, tail_file, head_file, file_info
    - System Info: disk_usage, memory_usage, process_list, uptime_info
    - Network: network_interfaces, ping_host
    - Core: execute_ssh_command, test_ssh_connection, execute_multiple_commands
    """
    
    # ============ BASIC INFO TOOLS ============
    
    @mcp.tool()
    async def whoami(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get current user information on remote server."""
        return await server.whoami(host, user, password, pkey_str, port)
    
    @mcp.tool()
    async def pwd(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get current working directory on remote server."""
        return await server.pwd(host, user, password, pkey_str, port)
    
    @mcp.tool()
    async def hostname_info(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get hostname of remote server."""
        return await server.hostname_info(host, user, password, pkey_str, port)
    
    @mcp.tool()
    async def uname(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        flags: str = "-a",
    ) -> dict:
        """Get system information (kernel, architecture, etc.)."""
        return await server.uname(host, user, password, pkey_str, port, flags)
    
    # ============ FILE LISTING TOOLS ============
    
    @mcp.tool()
    async def ls(
        host: str,
        user: str,
        path: str = ".",
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        long_format: bool = False,
        all_files: bool = False,
        human_readable: bool = False,
    ) -> dict:
        """List directory contents on remote server."""
        return await server.ls(
            host, user, path, password, pkey_str, port,
            long_format, all_files, human_readable
        )
    
    @mcp.tool()
    async def tree(
        host: str,
        user: str,
        path: str = ".",
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        max_depth: int = None,
    ) -> dict:
        """Display directory tree structure on remote server."""
        return await server.tree(host, user, path, password, pkey_str, port, max_depth)
    
    # ============ FILE SEARCH TOOLS ============
    
    @mcp.tool()
    async def find_files(
        host: str,
        user: str,
        path: str = ".",
        name_pattern: str = None,
        file_type: str = None,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        max_depth: int = None,
    ) -> dict:
        """
        Find files matching criteria on remote server.
        
        Args:
            name_pattern: Filename pattern (e.g., "*.txt", "test*")
            file_type: File type (f=file, d=directory, l=symlink)
            max_depth: Maximum search depth
        """
        return await server.find_files(
            host, user, path, name_pattern, file_type,
            password, pkey_str, port, max_depth
        )
    
    @mcp.tool()
    async def grep_files(
        host: str,
        user: str,
        pattern: str,
        path: str = ".",
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        recursive: bool = True,
        case_insensitive: bool = False,
        show_line_numbers: bool = True,
    ) -> dict:
        """Search for text pattern in files on remote server."""
        return await server.grep_files(
            host, user, pattern, path, password, pkey_str, port,
            recursive, case_insensitive, show_line_numbers
        )
    
    @mcp.tool()
    async def locate_file(
        host: str,
        user: str,
        pattern: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        limit: int = None,
    ) -> dict:
        """Quickly locate files by name using locate database."""
        return await server.locate_file(host, user, pattern, password, pkey_str, port, limit)
    
    # ============ FILE OPERATIONS TOOLS ============
    
    @mcp.tool()
    async def cat_file(
        host: str,
        user: str,
        file_path: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        lines: int = None,
    ) -> dict:
        """Display file contents from remote server."""
        return await server.cat_file(host, user, file_path, password, pkey_str, port, lines)
    
    @mcp.tool()
    async def tail_file(
        host: str,
        user: str,
        file_path: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        lines: int = 10,
    ) -> dict:
        """Display last N lines of file from remote server."""
        return await server.tail_file(host, user, file_path, password, pkey_str, port, lines)
    
    @mcp.tool()
    async def head_file(
        host: str,
        user: str,
        file_path: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        lines: int = 10,
    ) -> dict:
        """Display first N lines of file from remote server."""
        return await server.head_file(host, user, file_path, password, pkey_str, port, lines)
    
    @mcp.tool()
    async def file_info(
        host: str,
        user: str,
        path: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get detailed file/directory information (size, permissions, timestamps)."""
        return await server.file_info(host, user, path, password, pkey_str, port)
    
    # ============ SYSTEM INFO TOOLS ============
    
    @mcp.tool()
    async def disk_usage(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        human_readable: bool = True,
    ) -> dict:
        """Get disk usage information from remote server."""
        return await server.disk_usage(host, user, password, pkey_str, port, human_readable)
    
    @mcp.tool()
    async def memory_usage(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        human_readable: bool = True,
    ) -> dict:
        """Get memory usage information from remote server."""
        return await server.memory_usage(host, user, password, pkey_str, port, human_readable)
    
    @mcp.tool()
    async def process_list(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        user_filter: str = None,
    ) -> dict:
        """List running processes on remote server."""
        return await server.process_list(host, user, password, pkey_str, port, user_filter)
    
    @mcp.tool()
    async def uptime_info(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get system uptime and load average from remote server."""
        return await server.uptime_info(host, user, password, pkey_str, port)
    
    # ============ NETWORK TOOLS ============
    
    @mcp.tool()
    async def network_interfaces(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Get network interface information from remote server."""
        return await server.network_interfaces(host, user, password, pkey_str, port)
    
    @mcp.tool()
    async def ping_host(
        host: str,
        user: str,
        target: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        count: int = 4,
    ) -> dict:
        """Ping a target host from remote server."""
        return await server.ping_host(host, user, target, password, pkey_str, port, count)
    
    # ============ CORE TOOLS ============
    
    @mcp.tool()
    async def execute_ssh_command(
        host: str,
        user: str,
        command: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        wait: float = 0.5,
    ) -> dict:
        """Execute any SSH command on remote server."""
        return await server.execute_ssh_command(
            host, user, command, password, pkey_str, port, wait
        )
    
    @mcp.tool()
    async def test_ssh_connection(
        host: str,
        user: str,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
    ) -> dict:
        """Test SSH connection to remote server."""
        return await server.test_ssh_connection(host, user, password, pkey_str, port)
    
    @mcp.tool()
    async def execute_multiple_commands(
        host: str,
        user: str,
        commands: list,
        password: str = None,
        pkey_str: str = None,
        port: int = 22,
        wait: float = 0.5,
    ) -> dict:
        """Execute multiple commands in the same SSH session."""
        return await server.execute_multiple_commands(
            host, user, commands, password, pkey_str, port, wait
        )
