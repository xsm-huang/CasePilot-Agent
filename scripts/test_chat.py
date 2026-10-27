"""手动直连测试：读取 .env，只请求一次，不启动项目、不重试。"""

import os
import time
from pathlib import Path

import httpx
from casepilot.model.profiles import DEFAULT_CHAT_MODEL, chat_profile
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("ZHIPU_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("请先在项目 .env 中填写 ZHIPU_API_KEY。")
    profile = chat_profile(os.getenv("CHAT_MODEL", DEFAULT_CHAT_MODEL))

    print("开始请求智谱聊天接口，最多等待 120 秒，不重试。", flush=True)
    started = time.monotonic()
    try:
        response = httpx.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": profile.name,
                "messages": [{"role": "user", "content": "请只回复 OK"}],
                "stream": False,
                **profile.request_options("manual"),
            },
            timeout=120,
        )
        print(f"HTTP 状态码：{response.status_code}")
        print(response.text.replace(api_key, "[已隐藏密钥]"))
    except httpx.HTTPError as exc:
        print(f"请求失败：{type(exc).__name__}：{str(exc).replace(api_key, '[已隐藏密钥]')}")
        return 1
    finally:
        print(f"耗时：{time.monotonic() - started:.1f} 秒")
    return 0 if response.is_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
