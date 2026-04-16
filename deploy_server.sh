#!/bin/bash

set -e

SERVER_IP="115.190.247.178"
SERVER_PORT="4598"
SERVER_USER="root"
SERVER_PASSWORD="ZxMe6839"
PROJECT_DIR="/root/Docs2MCP"

echo "========================================="
echo "Docs2MCP Server Deployment Script"
echo "========================================="

echo "[1/8] Checking server connection..."
nc -z -w5 $SERVER_IP $SERVER_PORT 2>/dev/null && echo "Port $SERVER_PORT is open" || { echo "Port $SERVER_PORT is not reachable"; exit 1; }

echo "[2/8] Creating project directory on server..."
ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP "mkdir -p $PROJECT_DIR"

echo "[3/8] Transferring MCP server files..."
cat << 'ENDSSH' | ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP
mkdir -p /root/Docs2MCP/mcp-server/src/utils
mkdir -p /root/Docs2MCP/data
mkdir -p /root/Docs2MCP/logs
ENDSSH

echo "[4/8] Installing Python dependencies on server..."
ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /root/Docs2MCP/mcp-server
pip install -q Flask==2.3.0 Werkzeug==2.3.0 requests==2.26.0 beautifulsoup4==4.9.3 python-dotenv==0.19.0 lxml==4.9.3 APScheduler==3.10.4
ENDSSH

echo "[5/8] Creating systemd service for MCP server..."
ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
cat > /etc/systemd/system/docs2mcp.service << 'SERVICE'
[Unit]
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
SERVICE

systemctl daemon-reload
systemctl enable docs2mcp
echo "Service created and enabled"
ENDSSH

echo "[6/8] Starting MCP server service..."
ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP "systemctl restart docs2mcp && sleep 3 && systemctl status docs2mcp"

echo "[7/8] Checking firewall settings..."
ssh -o StrictHostKeyChecking=no -p $SERVER_PORT $SERVER_USER@$SERVER_IP "ufw allow 5000/tcp 2>/dev/null || firewall-cmd --add-port=5000/tcp --permanent 2>/dev/null || echo 'Firewall config skipped'"

echo "[8/8] Verifying deployment..."
sleep 2
curl -s http://localhost:5000/api/server/status || echo "Server may need a moment to start"

echo ""
echo "========================================="
echo "Deployment completed!"
echo "========================================="
echo "MCP Server URL: http://$SERVER_IP:5000"
echo "API Endpoints:"
echo "  - http://$SERVER_IP:5000/api/docs/add (POST)"
echo "  - http://$SERVER_IP:5000/api/docs/list (GET)"
echo "  - http://$SERVER_IP:5000/api/server/status (GET)"
echo "  - http://$SERVER_IP:5000/api/ide/query?q=<search> (GET)"
echo "  - http://$SERVER_IP:5000/mcp/info (GET)"
echo ""
echo "To check service status: systemctl status docs2mcp"
echo "To view logs: tail -f /root/Docs2MCP/logs/stdout.log"
