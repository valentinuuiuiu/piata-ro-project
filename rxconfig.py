import reflex as rx

config = rx.Config(
    app_name="piata_ro",
    api_url="http://localhost:8000",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
