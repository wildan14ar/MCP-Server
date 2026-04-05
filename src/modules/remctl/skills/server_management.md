# Server Management Skills

## Overview
This skill teaches how to manage remote servers via SSH using the remctl tools.

## Available Tools

### Core Tool
- `server_exec` - Execute any SSH command (requires approval)

### Filesystem Tools (All Require Approval)
- `server_ls` - List directory contents
- `server_pwd` - Print working directory
- `server_cd` - Change directory
- `server_mkdir` - Create directory
- `server_rm` - Remove file/directory (⚠️ dangerous)
- `server_cp` - Copy file/directory
- `server_mv` - Move/rename file
- `server_cat` - Read file content
- `server_head` - Read first N lines
- `server_tail` - Read last N lines
- `server_file_info` - Get file metadata (stat)
- `server_find` - Search files by name
- `server_grep` - Search content in files

### System Tools (All Require Approval)
- `server_whoami` - Get current user
- `server_hostname` - Get server hostname
- `server_uname` - Get system info (kernel, arch)
- `server_uptime` - Get uptime and load averages
- `server_ps` - List running processes
- `server_top` - Get top processes (by CPU/memory)
- `server_df` - Get disk space usage
- `server_free` - Get memory (RAM) usage
- `server_du` - Get directory size
- `server_network` - Get network interfaces
- `server_ping` - Ping a remote host
- `server_kill` - Kill process by PID (⚠️ dangerous)
- `server_killall` - Kill processes by name (⚠️ dangerous)
- `systemctl` - Manage systemd services (⚠️ dangerous)
- `server_logs` - View system logs

## Workflow: Server Exploration

### Step 1: Basic System Info
```
server_whoami() → "admin"
server_hostname() → "prod-web-01"
server_uptime() → "12:34:56 up 45 days, 2:30, 1 user"
server_uname() → "Linux prod-web-01 5.4.0..."
```

### Step 2: Check Resources
```
server_df() → Disk usage for all mounts
server_free() → Memory usage (total, used, free)
server_top(count=10, sort_by="cpu") → Top 10 CPU processes
```

### Step 3: File Exploration
```
server_pwd() → "/home/admin"
server_ls(path="/var/log", long_format=True) → Detailed file list
server_find(path="/var/log", name_pattern="*.log") → Find all log files
server_grep(pattern="error", path="/var/log/app.log") → Search for errors
```

## Example: Check Server Health

```
1. server_uptime() → Check load average
2. server_free() → Check memory usage
3. server_df() → Check disk space
4. server_logs(service_name="nginx", lines=50) → Check recent errors
```

## Example: Find and Fix Issue

```
1. server_top(count=20, sort_by="cpu") → Find high CPU process
2. server_ps() → Get full process list
3. server_logs(service_name="myservice", lines=100) → Check logs
4. systemctl(service_name="myservice", action="restart") → Restart if needed
```

## ⚠️ Warnings

1. **`server_rm`** - Permanently deletes files/directories
2. **`server_kill`** - Terminates processes immediately
3. **`systemctl stop/restart`** - Can make services unavailable
4. **`server_exec`** - Can run ANY command, use with caution

## Best Practices

1. **Read before writing** - Always check file content before modifying
2. **Use specific paths** - Avoid wildcard patterns that could affect many files
3. **Test commands first** - Use `server_exec` with safe commands before destructive ones
4. **Monitor after changes** - Check logs and service status after modifications
5. **Use systemctl for services** - Don't manually start/stop processes
