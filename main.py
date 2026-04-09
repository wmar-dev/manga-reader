import os

from dotenv import load_dotenv
from flask import Flask, g

import db as db_module
from helpers import cache, display_name, chapter_label

load_dotenv()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DB_PATH = os.environ.get("DB_PATH", "manga.db")

db_module.set_db_path(DB_PATH)

app = Flask(__name__)
cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


app.jinja_env.globals.update(display_name=display_name, chapter_label=chapter_label)

from views import bp  # noqa: E402 — imported after app/cache are defined
app.register_blueprint(bp)


if __name__ == "__main__":
    db_module.init_db()
    app.run(host=HOST, port=PORT, debug=True)
