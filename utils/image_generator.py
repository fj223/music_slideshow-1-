#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硅基流动 Kwai-Kolors 图像生成（OpenAI 兼容）
依赖：pip install openai
"""
import openai
import requests
from pathlib import Path
from datetime import datetime
import os
import httpx

# ========== 配置 ==========
SILICON_API_KEY = os.getenv("SILICON_API_KEY", "sk-swbvirjuyutfhjkzykvziqsoeoebazzaslyiyrcgqzypngml")
SILICON_BASE_URL = "https://api.siliconflow.cn/v1"          # 官方入口

for _k in ("HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy","NO_PROXY","no_proxy"):
    os.environ.pop(_k, None)
os.environ["NO_PROXY"] = "*"
_client = openai.OpenAI(api_key=SILICON_API_KEY, base_url=SILICON_BASE_URL, http_client=httpx.Client())

# ========== 生成函数 ==========
def generate_image(prompt: str,
                   size: str = "1024x1024",
                   save_dir: str = "output/images",
                   save_name: str = None) -> str:
    """生成单张图并下载到本地"""
    resp = _client.images.generate(
        model="Kwai-Kolors/Kolors",   # 硅基流动模型 ID
        prompt=prompt,
        size=size,
        n=1
    )
    img_url = resp.data[0].url

    Path(save_dir).mkdir(parents=True, exist_ok=True)
    file_name = save_name or f"kolors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = Path(save_dir) / file_name
    save_path.write_bytes(requests.get(img_url, timeout=30).content)

    print(f"[INFO] 图片已保存：{save_path}")
    return str(save_path)


# ========== 批量配图 ==========
def create_images_for_sentences(sentences: list[str],
                                style: str = "艺术风格",
                                max_imgs: int = 8) -> list[str]:
    paths = []
    for sent in sentences[:max_imgs]:
        prompt = f"{sent}，{style}，高清，8K"
        paths.append(generate_image(prompt))
    return paths


# ========== 自测 ==========
if __name__ == "__main__":
    generate_image("阳光明媚的夏日深林，金色雪山，碧蓝湖水，远处有高大的树木，苹果树结满了苹果，柔和的下午阳光，专业风光摄影，8K超高清，细节丰富")