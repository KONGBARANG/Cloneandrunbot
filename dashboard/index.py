from .dashboard import setup_routes


def init_app(app):
	"""Initialize the dashboard on the given aiohttp `app`.

	Example in your `main.py` after creating `app_web`:
		from dashboard.index import init_app
		init_app(app_web)
	"""
	setup_routes(app)

