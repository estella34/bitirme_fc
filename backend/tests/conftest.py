import os
import tempfile

# Motor içe aktarılırken oluşturulduğu için ortam değişkeni her şeyden önce ayarlanmalı.
os.environ["ENVANTER_DATA_DIR"] = tempfile.mkdtemp(prefix="envanter-test-")
os.environ["ENVANTER_CAMERA_ENABLED"] = "false"  # testler gerçek kameraya dokunmasın
os.environ["ENVANTER_WEB_DIST"] = os.path.join(os.environ["ENVANTER_DATA_DIR"], "no-web")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from envanter.main import create_app

    with TestClient(create_app()) as c:
        yield c
