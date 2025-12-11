import asyncio
from datetime import timedelta
import os
import secrets
import hashlib
import time
import socket
import struct
from functools import wraps
import threading
from flask import Flask, request, Response, session, redirect, url_for, render_template_string
from werkzeug.wrappers.response import Response as BaseResponse
import initialize
from python.helpers import files, git, mcp_server, fasta2a_server

# Try to import AG-UI, handle gracefully if not available
try:
    from python.agui.flask_integration import DynamicAGUIProxy
    AGUI_AVAILABLE = True
except Exception as e:
    AGUI_AVAILABLE = False
    DynamicAGUIProxy = None
from python.helpers.files import get_abs_path
from python.helpers import runtime, dotenv, process
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle
from python.helpers import login

# disable logging
import logging
logging.getLogger().setLevel(logging.WARNING)


# Set the new timezone to 'UTC'
os.environ["TZ"] = "UTC"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Apply the timezone change
if hasattr(time, 'tzset'):
    time.tzset()

# initialize the internal Flask server
webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
webapp.config.update(
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_NAME="session_" + runtime.get_runtime_id(),  # bind the session cookie name to runtime id to prevent session collision on same host
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)
)

lock = threading.Lock()

# CORS configuration for microservices architecture
try:
    from flask_cors import CORS
    
    # Get allowed origins from environment variable
    # Format: "https://app.vercel.app,https://yourdomain.com"
    cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
    
    if cors_origins_env:
        # Production: Use environment variable
        allowed_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    elif runtime.is_development():
        # Development: Allow local dev servers
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]
    else:
        # Production default: Empty (no CORS if not configured)
        allowed_origins = []
    
    if allowed_origins:
        CORS(webapp,
             resources={
                 r"/api/*": {
                     "origins": allowed_origins,
                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                     "allow_headers": ["Content-Type", "X-API-KEY", "X-CSRF-Token"],
                     "allow_credentials": False,  # Don't allow credentials for API
                     "max_age": 3600
                 },
                 r"/agui/*": {
                     "origins": allowed_origins,
                     "methods": ["GET", "POST", "OPTIONS"],
                     "allow_headers": ["Content-Type", "X-AGUI-Connection", "X-AGUI-Context"],
                     "allow_credentials": False,  # Don't allow credentials for AG-UI
                     "max_age": 3600
                 }
             })
        PrintStyle().print(f"CORS enabled for origins: {', '.join(allowed_origins)}")
    else:
        PrintStyle().warning("CORS not configured. Set CORS_ALLOWED_ORIGINS environment variable.")
except ImportError:
    PrintStyle().warning("flask-cors not installed. CORS disabled. Install with: pip install flask-cors")

@webapp.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    # Security headers for production
    if not runtime.is_development():
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Always add these headers
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    
    return response

# Set up basic authentication for UI and API but not MCP
# basic_auth = BasicAuth(webapp)


def is_loopback_address(address):
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0]
        >> (32 - 8)
        == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    address_type = "hostname"
    try:
        socket.inet_pton(socket.AF_INET6, address)
        address_type = "ipv6"
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET, address)
            address_type = "ipv4"
        except socket.error:
            address_type = "hostname"

    if address_type == "ipv4":
        return loopback_checker[socket.AF_INET](address)
    elif address_type == "ipv6":
        return loopback_checker[socket.AF_INET6](address)
    else:
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
            except socket.gaierror:
                return False
            for family, _, _, _, sockaddr in r:
                if not loopback_checker[family](sockaddr[0]):
                    return False
        return True

def requires_api_key(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Use the auth token from settings (same as MCP server)
        from python.helpers.settings import get_settings
        valid_api_key = get_settings()["mcp_server_token"]

        if api_key := request.headers.get("X-API-KEY"):
            if api_key != valid_api_key:
                return Response("Invalid API key", 401)
        elif request.json and request.json.get("api_key"):
            api_key = request.json.get("api_key")
            if api_key != valid_api_key:
                return Response("Invalid API key", 401)
        else:
            return Response("API key required", 401)
        return await f(*args, **kwargs)

    return decorated


# allow only loopback addresses
def requires_loopback(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        if not is_loopback_address(request.remote_addr):
            return Response(
                "Access denied.",
                403,
                {},
            )
        return await f(*args, **kwargs)

    return decorated


# require authentication for handlers
def requires_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        user_pass_hash = login.get_credentials_hash()
        # If no auth is configured, just proceed
        if not user_pass_hash:
            return await f(*args, **kwargs)

        if session.get('authentication') != user_pass_hash:
            # Check if this is an API request (external frontend)
            if request.path.startswith('/api/'):
                return Response(
                    '{"error": "Authentication required"}',
                    status=401,
                    mimetype='application/json'
                )
            # Otherwise redirect to login (for bundled UI)
            return redirect(url_for('login_handler'))
        
        return await f(*args, **kwargs)

    return decorated

def csrf_protect(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Skip CSRF for API routes with API key (API key is sufficient auth)
        if request.path.startswith('/api/'):
            api_key = request.headers.get("X-API-KEY") or (request.json and request.json.get("api_key"))
            if api_key:
                # API key authentication bypasses CSRF
                return await f(*args, **kwargs)
        
        # Otherwise enforce CSRF
        token = session.get("csrf_token")
        header = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get("csrf_token_" + runtime.get_runtime_id())
        sent = header or cookie
        if not token or not sent or token != sent:
            return Response("CSRF token missing or invalid", 403)
        return await f(*args, **kwargs)

    return decorated

@webapp.route("/login", methods=["GET", "POST"])
async def login_handler():
    error = None
    if request.method == 'POST':
        user = dotenv.get_dotenv_value("AUTH_LOGIN")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")
        
        if request.form['username'] == user and request.form['password'] == password:
            session['authentication'] = login.get_credentials_hash()
            return redirect(url_for('serve_index'))
        else:
            error = 'Invalid Credentials. Please try again.'
            
    login_page_content = files.read_file("webui/login.html")
    return render_template_string(login_page_content, error=error)

@webapp.route("/logout")
async def logout_handler():
    session.pop('authentication', None)
    return redirect(url_for('login_handler'))

# handle default address, load index
@webapp.route("/", methods=["GET"])
@requires_auth
async def serve_index():
    gitinfo = None
    try:
        gitinfo = git.get_git_info()
    except Exception:
        gitinfo = {
            "version": "unknown",
            "commit_time": "unknown",
        }
    index = files.read_file("webui/index.html")
    index = files.replace_placeholders_text(
        _content=index,
        version_no=gitinfo["version"],
        version_time=gitinfo["commit_time"]
    )
    return index

def run():
    PrintStyle().print("Initializing framework...")

    # Suppress only request logs but keep the startup messages
    from werkzeug.serving import WSGIRequestHandler
    from werkzeug.serving import make_server
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from a2wsgi import ASGIMiddleware

    PrintStyle().print("Starting server...")

    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
        def log_request(self, code="-", size="-"):
            pass  # Override to suppress request logging

    # Get configuration from environment
    port = runtime.get_web_ui_port()
    host = (
        runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "localhost"
    )
    server = None

    def register_api_handler(app, handler: type[ApiHandler]):
        name = handler.__module__.split(".")[-1]
        instance = handler(app, lock)

        async def handler_wrap() -> BaseResponse:
            return await instance.handle_request(request=request)

        if handler.requires_loopback():
            handler_wrap = requires_loopback(handler_wrap)
        if handler.requires_auth():
            handler_wrap = requires_auth(handler_wrap)
        if handler.requires_api_key():
            handler_wrap = requires_api_key(handler_wrap)
        if handler.requires_csrf():
            handler_wrap = csrf_protect(handler_wrap)

        # Register both legacy and prefixed routes for backward compatibility
        app.add_url_rule(
            f"/{name}",
            f"/{name}",
            handler_wrap,
            methods=handler.get_methods(),
        )

        app.add_url_rule(
            f"/api/{name}",
            f"/api/{name}",
            handler_wrap,
            methods=handler.get_methods(),
        )

    # initialize and register API handlers
    handlers = load_classes_from_folder("python/api", "*.py", ApiHandler)
    for handler in handlers:
        register_api_handler(webapp, handler)

    # add the webapp, mcp, a2a, and agui to the app
    middleware_routes = {
        "/mcp": ASGIMiddleware(app=mcp_server.DynamicMcpProxy.get_instance()),  # type: ignore
        "/a2a": ASGIMiddleware(app=fasta2a_server.DynamicA2AProxy.get_instance()),  # type: ignore
    }
    
    # Add AG-UI if available and enabled
    if AGUI_AVAILABLE and DynamicAGUIProxy:
        agui_proxy = DynamicAGUIProxy.get_instance()
        agui_proxy.initialize()
        middleware_routes["/agui"] = ASGIMiddleware(app=agui_proxy)  # type: ignore

    app = DispatcherMiddleware(webapp, middleware_routes)  # type: ignore

    PrintStyle().debug(f"Starting server at http://{host}:{port} ...")

    server = make_server(
        host=host,
        port=port,
        app=app,
        request_handler=NoRequestLoggingWSGIRequestHandler,
        threaded=True,
    )
    process.set_server(server)
    server.log_startup()

    # Start init_a0 in a background thread when server starts
    # threading.Thread(target=init_a0, daemon=True).start()
    init_a0()

    # run the server
    server.serve_forever()


def init_a0():
    # initialize contexts and MCP
    init_chats = initialize.initialize_chats()
    # only wait for init chats, otherwise they would seem to disappear for a while on restart
    init_chats.result_sync()

    initialize.initialize_mcp()
    # start job loop
    initialize.initialize_job_loop()
    # preload
    initialize.initialize_preload()



# run the internal server
if __name__ == "__main__":
    runtime.initialize()
    dotenv.load_dotenv()
    run()