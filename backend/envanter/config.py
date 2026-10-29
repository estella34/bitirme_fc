from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ortam değişkenleri `ENVANTER_` önekiyle okunur (ör. ENVANTER_DATA_DIR=/data/envanter)."""

    model_config = SettingsConfigDict(env_prefix="ENVANTER_", env_file=".env", extra="ignore")

    # Görüntüler, küçük resimler ve SQLite dosyası burada durur. Jetson'da /data altına alın.
    data_dir: Path = Path("./var")
    database_url: str | None = None

    # Derlenmiş arayüz (web/dist). Varsa aynı sunucudan servis edilir.
    web_dist: Path = Path(__file__).resolve().parents[2] / "web" / "dist"

    thumbnail_px: int = 480
    # Barkod çözücü tam görüntüde bir şey bulamazsa klasik ön işlemeyle (B1) yeniden dener.
    decode_fallback: bool = True
    # Kamera (Jetson CSI, Arducam CamArray + 4×IMX519). None: /dev/video0 ve i2ctransfer
    # varsa otomatik açılır; Mac'te kendiliğinden kapalıdır.
    camera_enabled: bool | None = None
    camera_i2c_bus: int = 10
    camera_channel: int = 0  # 0: 4 kamera birleşik (2x2), 1..4: tek kamera kanalı
    camera_width: int = 3840
    camera_height: int = 2160
    camera_fps: int = 17
    # Bu kadar saniye kimse izlemez/çekmezse kamera bırakılır.
    camera_idle_s: float = 20.0
    # Arayüzün geliştirme sunucusu (Vite) için izin verilen köken.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def captures_dir(self) -> Path:
        return self.data_dir / "captures"

    @property
    def db_url(self) -> str:
        return self.database_url or f"sqlite:///{(self.data_dir / 'envanter.db').resolve()}"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.captures_dir.mkdir(parents=True, exist_ok=True)
    return s
