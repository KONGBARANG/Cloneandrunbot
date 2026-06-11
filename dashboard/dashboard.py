import os
import platform
import datetime
from aiohttp import web

_START_TIME = datetime.datetime.now(datetime.UTC)


async def dashboard_page(request: web.Request) -> web.Response:
		"""Return a simple HTML dashboard page with basic runtime info."""
		uptime = datetime.datetime.now(datetime.UTC) - _START_TIME
		bot_token = os.environ.get("BOT_TOKEN") or os.environ.get("TOKEN") or ""
		if bot_token:
				masked = bot_token[:4] + "..." + bot_token[-4:] if len(bot_token) > 8 else "hidden"
		else:
				masked = "not-set"

		html = f"""<!doctype html>
<html>
	<head>
		<meta charset="utf-8">
		<title>Global-System Dashboard</title>
		<style>
			body{{font-family:Arial,Helvetica,sans-serif;margin:20px}}
			.card{{border:1px solid #e1e1e1;padding:16px;border-radius:6px;max-width:900px}}
			.row{{display:flex;gap:16px;flex-wrap:wrap}}
			.item{{min-width:200px}}
		</style>
	</head>
	<body>
		<h1>Global-System Dashboard</h1>
		<div class="card">
			<div class="row">
				<div class="item"><strong>Service:</strong> Global-System Bot</div>
				<div class="item"><strong>Uptime:</strong> {str(uptime).split('.')[0]}</div>
				<div class="item"><strong>Python:</strong> {platform.python_version()}</div>
				<div class="item"><strong>Host:</strong> {platform.node()}</div>
			</div>
			<hr/>
			<div class="row">
				<div class="item"><strong>Port:</strong> {os.environ.get('PORT', '8080')}</div>
				<div class="item"><strong>Bot Token:</strong> {masked}</div>
				<div class="item"><a href="/dashboard/status">Status (JSON)</a></div>
			</div>
		</div>
	</body>
</html>"""

		return web.Response(text=html, content_type="text/html")


async def status_api(request: web.Request) -> web.Response:
		"""Return a small JSON status useful for automated checks."""
		uptime = datetime.datetime.now(datetime.UTC) - _START_TIME
		data = {
				"service": "Global-System Bot",
				"uptime": str(uptime).split('.')[0],
				"python_version": platform.python_version(),
				"host": platform.node(),
				"port": int(os.environ.get("PORT", 8080)),
				"time": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
		}
		return web.json_response(data)


def setup_routes(app: web.Application) -> None:
		"""Register dashboard routes on an aiohttp `app`.

		Call `setup_routes(app)` from your main web setup to enable `/dashboard`.
		"""
		app.router.add_get("/dashboard", dashboard_page)
		app.router.add_get("/dashboard/status", status_api)
