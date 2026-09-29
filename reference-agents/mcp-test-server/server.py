"""最小 MCP over HTTP 测试服务器：实现 initialize/tools/list/tools/call"""
import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

TOOLS = [
    {
        "name": "echo",
        "description": "Echo the input message",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"]
        }
    },
    {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"]
        }
    }
]

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            return

        method = req.get("method", "")
        req_id = req.get("id")
        result = None

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-mcp-server", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments", {})
            if name == "echo":
                content = [{"type": "text", "text": args.get("message", "")}]
            elif name == "add":
                content = [{"type": "text", "text": str(args.get("a", 0) + args.get("b", 0))}]
            else:
                content = [{"type": "text", "text": f"Unknown tool: {name}"}]
            result = {"content": content, "isError": False}
        elif method == "notifications/initialized":
            self.send_response(200)
            self.end_headers()
            return
        else:
            result = {"error": f"Unknown method: {method}"}

        resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), MCPHandler)
    print("MCP test server running on port 8000")
    server.serve_forever()
