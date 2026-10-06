import argparse
from .core.config import Settings
from .persistence.db import DB
from .market.twelvedata import TwelveDataProvider
from .application import Analyzer
from .telegram.renderers import pulse
from .telegram.webhook import application


def frames(s, p):
    return {
        tf: p.candles(s.symbol, tf, 200)
        for tf in ("5min", "15min", "1h", "4h", "1day")
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--webhook", action="store_true")
    args = parser.parse_args()

    settings = Settings()

    if args.webhook:
        print("ARESTRADA V4 WEBHOOK ENTRYPOINT")
        print("Passenger/WSGI application:", application.__name__)
        return

    if args.health:
        DB(settings.db_path)
        print(
            "ARESTRADA V4 HEALTHY\n"
            "DB: OK\n"
            "Safety: fail-closed\n"
            "Provider key:",
            "SET" if settings.api_key else "MISSING",
            "\nTelegram:",
            "SET" if settings.bot_token else "MISSING",
            "\nPayments:",
            "ENABLED" if settings.payment_enabled else "DISABLED",
        )
        return

    provider = TwelveDataProvider(settings.api_key, settings.api_timeout)
    analyzer = Analyzer(
        settings.news_status,
        settings.news_fail_closed,
        settings.trade_min_score,
    )

    if args.once:
        result = analyzer.analyze(frames(settings, provider))
        print(pulse(result))
        return

    if args.poll:
        raise SystemExit(
            "Polling is not the primary deployment path. "
            "Use Passenger/WSGI with passenger_wsgi.py and telegram.webhook."
        )

    parser.print_help()


if __name__ == "__main__":
    main()
