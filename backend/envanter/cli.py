"""Komut satırı: `depogoz serve`, `depogoz demo-world`."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="depogoz", description="DepoGöz depo envanter sistemi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="API + arayüz sunucusunu başlat")
    serve.add_argument("--host", default="0.0.0.0", help="Jetson'da ağdan erişim için 0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument(
        "--reload", action="store_true", help="geliştirme: kod değişince yeniden yükle"
    )

    sub.add_parser("demo-world", help="Demo deposunu veritabanına ekle")

    args = parser.parse_args()
    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("envanter.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.cmd == "demo-world":
        from .db import init_db
        from .services.demo import ensure_demo_world

        init_db()
        print(f"Demo deposu hazır (id={ensure_demo_world()})")


if __name__ == "__main__":
    main()
