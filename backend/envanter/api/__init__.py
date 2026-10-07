from fastapi import APIRouter

from . import camera, live, robot, scans, tools, warehouses

router = APIRouter(prefix="/api")
router.include_router(warehouses.router)
router.include_router(scans.router)
router.include_router(robot.router)
router.include_router(tools.router)
router.include_router(live.router)
router.include_router(camera.router)
