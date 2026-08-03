#!/usr/bin/env python3
"""独立的尚书省 Excel / ch2t7 数据对比可视化服务。"""

import argparse
import importlib.util
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
VIS_ROOT = HERE.parent
REPO_ROOT = VIS_ROOT.parent
CURRENT_SERVER_PATH = VIS_ROOT / "ch2t7-design-vis/server.py"


def _load_current_data_module():
    spec = importlib.util.spec_from_file_location(
        "ch2t7_current_data_server", CURRENT_SERVER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法载入现有数据服务: {CURRENT_SERVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CURRENT_DATA = _load_current_data_module()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIS_ROOT), **kwargs)

    def _send_json(self, payload: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/shangshu-excel-comparison/")
            self.end_headers()
            return
        if path == "/api/current-data":
            self._send_json(CURRENT_DATA.get_payload())
            return
        if path == "/api/meta":
            payload = json.dumps(
                {
                    "excel": str(VIS_ROOT / "副本尚书省下机构官职表总表.xlsx"),
                    "database": str(
                        REPO_ROOT
                        / "data/database/song_bureaucracy_entries_ch2t7.db"
                    ),
                    "comparison": "实时读取当前 ch2t7 数据库；Excel 数据由原工作簿提取，不改动原文件。",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self._send_json(payload)
            return
        return super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8060)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        f"[shangshu-compare] http://{args.host}:{args.port}/shangshu-excel-comparison/",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()

