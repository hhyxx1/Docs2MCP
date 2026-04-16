#!/usr/bin/env python3

import os
import sys
import time
import subprocess

SERVER_IP = "115.190.247.178"
SERVER_PORT = "4598"
SERVER_USER = "root"
SERVER_PASSWORD = "ZxMe6839"
PROJECT_DIR = "/root/Docs2MCP"

LOCAL_MCP_SERVER = "/home/hyx/Projects/Docs2MCP/mcp-server"

def run_cmd(cmd, check=True):
    print(f"Running: {cmd[:80]}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
    return result

def cmd_on_server(command):
    full_cmd = f'''sshpass -p '{SERVER_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SERVER_PORT} {SERVER_USER}@{SERVER_IP} "{command.replace('"', '\\"')}"'''
    result = run_cmd(full_cmd, check=False)
    return result

def cmd_on_server_interactive(command):
    full_cmd = f'''sshpass -p '{SERVER_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SERVER_PORT} {SERVER_USER}@{SERVER_IP} "{command}"'''
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result

def main():
    print("=" * 50)
    print("Docs2MCP Server Deployment")
    print("=" * 50)

    print("\n[1/8] Testing server connection...")
    result = cmd_on_server("echo 'Connection OK' && pwd")
    if "Connection OK" not in result.stdout:
        print(f"Failed to connect: {result.stderr}")
        return False
    print("Connection successful!")

    print("\n[2/8] Creating directories on server...")
    cmd_on_server(f"mkdir -p {PROJECT_DIR}/mcp-server/src/utils")
    cmd_on_server(f"mkdir -p {PROJECT_DIR}/data")
    cmd_on_server(f"mkdir -p {PROJECT_DIR}/logs")
    print("Directories created")

    print("\n[3/8] Uploading MCP server files...")
    os.chdir(LOCAL_MCP_SERVER)

    for root, dirs, files in os.walk("src"):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, "src")
            remote_path = f"{PROJECT_DIR}/mcp-server/src/{rel_path}"
            remote_dir = os.path.dirname(remote_path)

            cmd_on_server(f"mkdir -p '{remote_dir}'")

            print(f"  Uploading {rel_path}...")
            result = run_cmd(f'''sshpass -p '{SERVER_PASSWORD}' scp -P {SERVER_PORT} -o StrictHostKeyChecking=no '{local_path}' {SERVER_USER}@{SERVER_IP}:'{remote_path}' ''', check=False)
            if result.returncode != 0:
                print(f"  Failed to upload {rel_path}")

    print("\n[4/8] Uploading requirements.txt...")
    run_cmd(f'''sshpass -p '{SERVER_PASSWORD}' scp -P {SERVER_PORT} -o StrictHostKeyChecking=no requirements.txt {SERVER_USER}@{SERVER_IP}:{PROJECT_DIR}/mcp-server/''')

    print("\n[5/8] Installing Python dependencies on server...")
    install_cmd = f"cd {PROJECT_DIR}/mcp-server && pip3 install -q Flask==2.3.0 Werkzeug==2.3.0 requests==2.26.0 beautifulsoup4==4.9.3 python-dotenv==0.19.0 lxml==4.9.3 APScheduler==3.10.4"
    result = cmd_on_server_interactive(install_cmd)
    print(f"  Install result: {result.stdout[:200] if result.stdout else 'OK'}")

    print("\n[6/8] Creating systemd service...")
    service_content = """[Unit]
Description=Docs2MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Docs2MCP/mcp-server/src
ExecStart=/usr/bin/python3 /root/Docs2MCP/mcp-server/src/app.py
Restart=always
RestartSec=10
StandardOutput=append:/root/Docs2MCP/logs/stdout.log
StandardError=append:/root/Docs2MCP/logs/stderr.log

[Install]
WantedBy=multi-user.target
"""

    service_content_escaped = service_content.replace("\n", "\\\\n")
    cmd_on_server(f"cat > /etc/systemd/system/docs2mcp.service << 'EOF'\n{service_content}\nEOF")

    cmd_on_server("systemctl daemon-reload")
    cmd_on_server("systemctl enable docs2mcp")
    print("Service created and enabled")

    print("\n[7/8] Starting MCP server...")
    cmd_on_server("systemctl restart docs2mcp")
    time.sleep(3)

    status = cmd_on_server("systemctl is-active docs2mcp")
    if "active" in status.stdout:
        print("MCP Server is running!")
    else:
        print("Server may still be starting...")

    print("\n[8/8] Checking firewall...")
    cmd_on_server("ufw allow 5000/tcp 2>/dev/null || firewall-cmd --add-port=5000/tcp --permanent 2>/dev/null || echo 'Firewall config skipped'")

    print("\n" + "=" * 50)
    print("Deployment completed!")
    print("=" * 50)
    print(f"MCP Server URL: http://{SERVER_IP}:5000")
    print("\nAPI Endpoints:")
    print(f"  - http://{SERVER_IP}:5000/api/docs/add (POST)")
    print(f"  - http://{SERVER_IP}:5000/api/docs/list (GET)")
    print(f"  - http://{SERVER_IP}:5000/api/server/status (GET)")
    print(f"  - http://{SERVER_IP}:5000/api/ide/query?q=<search> (GET)")
    print(f"  - http://{SERVER_IP}:5000/mcp/info (GET)")
    print("\nTo check status: ssh root@115.190.247.178 -p 4598 'systemctl status docs2mcp'")
    print("To view logs: ssh root@115.190.247.178 -p 4598 'tail -f /root/Docs2MCP/logs/stdout.log'")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
