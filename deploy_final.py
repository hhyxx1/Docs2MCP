#!/usr/bin/env python3
import os
import sys
import subprocess
import select
import time
import termios
import tty

SERVER_IP = "115.190.247.178"
SERVER_PORT = "4598"
SERVER_USER = "root"
SERVER_PASSWORD = "ZxMe6839"
PROJECT_DIR = "/root/Docs2MCP"
LOCAL_PROJECT = "/home/hyx/Projects/Docs2MCP"

def send_command(child, cmd, wait_time=1):
    child.send(cmd + '\r')
    time.sleep(wait_time)

def expect_prompt(child, timeout=30):
    output = b""
    start = time.time()
    while time.time() - start < timeout:
        r, _, _ = select.select([child], [], [], 0.1)
        if r:
            data = child.recv(4096)
            output += data
            if b"$ " in output or b"# " in output or b"> " in output:
                break
    return output.decode('utf-8', errors='replace')

def main():
    print("=" * 50)
    print("Docs2MCP Deployment Script")
    print("=" * 50)

    # Create SSH command
    ssh_cmd = [
        'sshpass', '-p', SERVER_PASSWORD,
        'ssh', '-o', 'StrictHostKeyChecking=no',
        '-p', SERVER_PORT,
        f'{SERVER_USER}@{SERVER_IP}'
    ]

    print("\n[Step 1] Checking connection...")
    try:
        result = subprocess.run(
            ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
             '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}', 'echo OK'],
            capture_output=True, text=True, timeout=10
        )
        if 'OK' in result.stdout:
            print("Connection successful!")
        else:
            print(f"Connection failed: {result.stderr}")
            return
    except FileNotFoundError:
        print("sshpass not found. Installing...")
        subprocess.run(['brew', 'install', 'sshpass'], capture_output=True)
        return

    print("\n[Step 2] Creating directories...")
    subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         'mkdir -p /root/Docs2MCP/mcp-server/src/utils /root/Docs2MCP/data /root/Docs2MCP/logs'],
        check=True
    )

    print("\n[Step 3] Uploading server files...")
    os.chdir(LOCAL_PROJECT)

    for root, dirs, files in os.walk('mcp-server'):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, 'mcp-server')
            remote_path = f'/root/Docs2MCP/mcp-server/{rel_path}'
            remote_dir = os.path.dirname(remote_path)

            subprocess.run(
                ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
                 '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
                 f'mkdir -p "{remote_dir}"'],
                capture_output=True
            )

            subprocess.run(
                ['sshpass', '-p', SERVER_PASSWORD, 'scp', '-o', 'StrictHostKeyChecking=no',
                 '-P', SERVER_PORT, local_path,
                 f'{SERVER_USER}@{SERVER_IP}:{remote_path}'],
                capture_output=True
            )
            print(f"  Uploaded: {rel_path}")

    print("\n[Step 4] Creating venv and installing dependencies...")
    result = subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         'python3 -m venv /root/Docs2MCP/venv && /root/Docs2MCP/venv/bin/pip install Flask==2.3.0 Werkzeug==2.3.0 requests==2.26.0 beautifulsoup4==4.9.3 python-dotenv==0.19.0 lxml==4.9.3 APScheduler==3.10.4'],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"Installation error: {result.stderr[:200]}")
    else:
        print("Dependencies installed!")

    print("\n[Step 5] Creating systemd service...")
    service_content = """[Unit]
Description=Docs2MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Docs2MCP/mcp-server/src
ExecStart=/root/Docs2MCP/venv/bin/python /root/Docs2MCP/mcp-server/src/app.py
Restart=always
RestartSec=10
StandardOutput=append:/root/Docs2MCP/logs/stdout.log
StandardError=append:/root/Docs2MCP/logs/stderr.log

[Install]
WantedBy=multi-user.target
"""
    subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         f'cat > /etc/systemd/system/docs2mcp.service << EOF\n{service_content}EOF'],
        capture_output=True, text=True
    )

    subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         'systemctl daemon-reload && systemctl enable docs2mcp'],
        capture_output=True
    )

    print("\n[Step 6] Starting server...")
    result = subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         'systemctl restart docs2mcp && sleep 5 && systemctl status docs2mcp --no-pager'],
        capture_output=True, text=True, timeout=30
    )
    print(result.stdout[-500:] if result.stdout else "Starting...")

    print("\n[Step 7] Testing API...")
    result = subprocess.run(
        ['sshpass', '-p', SERVER_PASSWORD, 'ssh', '-o', 'StrictHostKeyChecking=no',
         '-p', SERVER_PORT, f'{SERVER_USER}@{SERVER_IP}',
         'curl -s http://localhost:5000/api/server/status'],
        capture_output=True, text=True, timeout=10
    )
    print(f"API Response: {result.stdout}")

    print("\n" + "=" * 50)
    print("Deployment completed!")
    print("=" * 50)
    print(f"MCP Server: http://{SERVER_IP}:5000")
    print(f"API Docs: http://{SERVER_IP}:5000/api/docs/list")

if __name__ == "__main__":
    main()
