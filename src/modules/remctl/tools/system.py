"""
System Tools - Server information and monitoring.

Provides tools for:
- System info (whoami, hostname, uname, uptime)
- Process monitoring (ps, top, kill)
- Resource usage (df, free, du)
- Network information

NOTE: All tools require user approval before execution.
"""

from typing import Optional, List, Dict, Any
from ..config.session import RemctlSession
from ..config.tools import tool
from ...lib.gatekeeper import gatekeeper


@tool(name="server_whoami")
async def get_current_user(session_id: str) -> dict:
    """
    Get current SSH user.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_whoami", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "whoami")
    return result


@tool(name="server_hostname")
async def get_hostname(session_id: str) -> dict:
    """
    Get server hostname.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_hostname", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "hostname")
    return result


@tool(name="server_uname")
async def get_system_info(session_id: str) -> dict:
    """
    Get detailed system information (kernel, architecture, etc.).

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_uname", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "uname -a")
    return result


@tool(name="server_uptime")
async def get_uptime(session_id: str) -> dict:
    """
    Get server uptime and load averages.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_uptime", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "uptime")
    return result


@tool(name="server_ps")
async def list_processes(
    session_id: str,
    show_all: bool = True,
    detailed: bool = True,
) -> dict:
    """
    List running processes.

    Requires user approval before execution.
    """
    cmd = "ps"
    if show_all and detailed:
        cmd += " aux"
    elif show_all:
        cmd += " -e"
    else:
        cmd += " -l"

    request = gatekeeper.create_request("server_ps", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_top")
async def get_top_processes(
    session_id: str,
    count: int = 20,
    sort_by: str = "cpu",
) -> dict:
    """
    Get top processes by CPU or memory usage.

    Requires user approval before execution.
    """
    # Use ps and sort
    if sort_by == "cpu":
        cmd = f"ps aux --sort=-%cpu | head -n {count + 1}"
    elif sort_by == "memory":
        cmd = f"ps aux --sort=-%mem | head -n {count + 1}"
    else:
        cmd = f"ps aux | head -n {count + 1}"

    request = gatekeeper.create_request("server_top", {"session_id": session_id, "count": count, "sort_by": sort_by})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_df")
async def get_disk_usage(
    session_id: str,
    human_readable: bool = True,
    path: Optional[str] = None,
) -> dict:
    """
    Get disk space usage.

    Requires user approval before execution.
    """
    cmd = "df"
    if human_readable:
        cmd += " -h"
    if path:
        cmd += f" {path}"

    request = gatekeeper.create_request("server_df", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_free")
async def get_memory_usage(session_id: str) -> dict:
    """
    Get memory (RAM) usage.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_free", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, "free -h")
    return result


@tool(name="server_du")
async def get_directory_size(
    session_id: str,
    path: str = ".",
    max_depth: int = 1,
    human_readable: bool = True,
) -> dict:
    """
    Get disk usage for a specific directory.

    Requires user approval before execution.
    """
    cmd = "du"
    if human_readable:
        cmd += " -h"
    cmd += f" --max-depth={max_depth}"
    cmd += f" {path}"

    request = gatekeeper.create_request("server_du", {"session_id": session_id, "path": path})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_network")
async def get_network_info(session_id: str) -> dict:
    """
    Get network interfaces and IP addresses.

    Requires user approval before execution.
    """
    # Try ip command first, fallback to ifconfig
    cmd = "ip addr show 2>/dev/null || ifconfig"

    request = gatekeeper.create_request("server_network", {"session_id": session_id})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result


@tool(name="server_ping")
async def ping_host(
    session_id: str,
    host: str,
    count: int = 4,
) -> dict:
    """
    Ping a remote host to check connectivity.

    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_ping", {"session_id": session_id, "host": host})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"ping -c {count} {host}")
    return result


@tool(name="server_kill")
async def kill_process(
    session_id: str,
    pid: int,
    signal: str = "TERM",
) -> dict:
    """
    Kill a process by PID.

    ⚠️ WARNING: This will terminate the process!
    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_kill", {"session_id": session_id, "pid": pid, "signal": signal})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"kill -{signal} {pid}")
    return result


@tool(name="server_killall")
async def kill_process_by_name(
    session_id: str,
    process_name: str,
    signal: str = "TERM",
) -> dict:
    """
    Kill all processes by name.

    ⚠️ WARNING: This will terminate all matching processes!
    Requires user approval before execution.
    """
    request = gatekeeper.create_request("server_killall", {"session_id": session_id, "process_name": process_name})

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"killall -{signal} {process_name}")
    return result


@tool(name="systemctl")
async def manage_service(
    session_id: str,
    service_name: str,
    action: str = "status",
) -> dict:
    """
    Manage systemd services (start, stop, restart, status).

    ⚠️ WARNING: Starting/stopping services can affect server availability!
    Requires user approval before execution.

    Args:
        session_id: Session ID
        service_name: Service name (e.g., nginx, mysql)
        action: Action to perform (status, start, stop, restart, enable, disable)
    """
    valid_actions = ["status", "start", "stop", "restart", "enable", "disable", "is-active", "is-enabled"]
    if action not in valid_actions:
        return {"status": "error", "message": f"Invalid action. Use: {', '.join(valid_actions)}"}

    request = gatekeeper.create_request("systemctl", {
        "session_id": session_id,
        "service_name": service_name,
        "action": action
    })

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, f"systemctl {action} {service_name}")
    return result


@tool(name="server_logs")
async def view_system_logs(
    session_id: str,
    service_name: Optional[str] = None,
    lines: int = 50,
    follow: bool = False,
) -> dict:
    """
    View system logs (journalctl or syslog).

    Requires user approval before execution.
    """
    if service_name:
        cmd = f"journalctl -u {service_name} -n {lines} --no-pager"
        if follow:
            cmd = f"journalctl -u {service_name} -f"
    else:
        cmd = f"tail -n {lines} /var/log/syslog 2>/dev/null || tail -n {lines} /var/log/messages"

    request = gatekeeper.create_request("server_logs", {
        "session_id": session_id,
        "service_name": service_name,
        "lines": lines
    })

    approval = await gatekeeper.wait_for_approval(request.request_id)
    if not approval["approved"]:
        return {"status": "rejected", "reason": approval["reason"]}

    result = RemctlSession.execute(session_id, cmd)
    return result
