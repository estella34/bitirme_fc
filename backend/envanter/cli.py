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

    sheet = sub.add_parser("print-sheet", help="Yazdırılabilir A4 test şablonu oluştur (PDF/PNG)")
    sheet.add_argument("-o", "--output", default="depogoz_test_sayfasi.pdf", help="Çıktı dosya yolu")
    sheet.add_argument("--format", default="PDF", choices=["PDF", "PNG"], help="Dosya biçimi")

    bench = sub.add_parser("benchmark", help="Bozuk/hasarlı QR okuma dayanıklılık testini çalıştır")
    bench.add_argument("--code", default="KL-992104", help="Test edilecek etiket metni")

    args = parser.parse_args()
    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("envanter.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.cmd == "demo-world":
        from .db import init_db
        from .services.demo import ensure_demo_world

        init_db()
        print(f"Demo deposu hazır (id={ensure_demo_world()})")
    elif args.cmd == "print-sheet":
        from .services.test_sheet import save_test_sheet

        out = save_test_sheet(args.output, fmt=args.format)
        print(f"Yazdırılabilir test sayfası oluşturuldu: {out.resolve()}")
    elif args.cmd == "benchmark":
        from .services.qr_benchmark import print_benchmark_table, run_benchmark

        print(f"'{args.code}' etiketi için dayanıklılık benchmarkı çalıştırılıyor...")
        results = run_benchmark(sample_text=args.code)
        print_benchmark_table(results)


if __name__ == "__main__":
    main()
