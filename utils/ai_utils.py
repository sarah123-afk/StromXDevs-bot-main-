"""AI helpers using plain HTTP so StromXDevs can run on Termux/Android.

The original project used the OpenAI Python SDK. That SDK pulls in jiter,
which can require a Rust build that is not available for many Termux setups.
This module talks to the same OpenAI-compatible chat-completions endpoint
using aiohttp instead, so the openai/jiter packages are not required.
"""
from __future__ import annotations

import aiohttp
import asyncio
import io
import json
import os
import random
import re
import time
from html import unescape
from langdetect import detect
from gtts import gTTS
from urllib.parse import quote, urlencode
from utils.config_loader import load_current_language, config
from dotenv import load_dotenv

load_dotenv()

current_language = load_current_language()
internet_access = config.get("INTERNET_ACCESS", True)
API_BASE_URL = os.getenv("AI_API_BASE_URL", config.get("API_BASE_URL", "")).rstrip("/")
API_KEY = (
    os.getenv("AI_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or config.get("API_KEY", "")
)
MODEL_ID = os.getenv("AI_MODEL_ID", config.get("MODEL_ID", ""))


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def _endpoint() -> str:
    base = API_BASE_URL
    if not base:
        raise RuntimeError("API_BASE_URL is not configured in config.yml")
    return f"{base}/chat/completions"


async def _chat_completion(payload: dict) -> dict:
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(_endpoint(), headers=_headers(), json=payload) as response:
            body = await response.text()
            if response.status >= 400:
                raise RuntimeError(f"AI API returned HTTP {response.status}: {body[:500]}")
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"AI API returned invalid JSON: {body[:500]}") from exc


async def generate_response(instructions, history):
    messages = [
        {"role": "system", "name": "instructions", "content": instructions},
        *history,
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "searchtool",
                "description": "Searches the internet.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The query for search engine"}},
                    "required": ["query"],
                },
            },
        }
    ]

    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    data = await _chat_completion(payload)
    response_message = data["choices"][0]["message"]
    tool_calls = response_message.get("tool_calls") or []

    if tool_calls:
        messages.append(response_message)
        available_functions = {"searchtool": duckduckgotool}
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            function_to_call = available_functions.get(function_name)
            if function_to_call is None:
                continue
            function_args = json.loads(tool_call["function"].get("arguments", "{}"))
            function_response = await function_to_call(query=function_args.get("query", ""))
            messages.append({
                "tool_call_id": tool_call.get("id", ""),
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })

        second_response = await _chat_completion({"model": MODEL_ID, "messages": messages})
        return second_response["choices"][0]["message"].get("content", "")

    return response_message.get("content", "")


def _strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return unescape(re.sub(r"\\s+", " ", value)).strip()


async def duckduckgotool(query) -> str:
    if not config.get("INTERNET_ACCESS", True):
        return "internet access has been disabled by user"
    query = str(query or "").strip()
    if not query:
        return "No search query was provided."

    url = "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                html = await response.text()
        results = []
        for match in re.finditer(r'<div[^>]+class="result".*?</div>\\s*</div>', html, re.I | re.S):
            block = match.group(0)
            title_match = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.I | re.S)
            snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', block, re.I | re.S)
            if title_match:
                title = _strip_html(title_match.group(1))
                snippet = _strip_html(snippet_match.group(1)) if snippet_match else ""
                results.append((title, snippet))
            if len(results) >= int(config.get("MAX_SEARCH_RESULTS", 4)):
                break
        if not results:
            return "No search results found."
        return "\n\n".join(f"[{i}] Title: {title}\nSnippet: {snippet}" for i, (title, snippet) in enumerate(results))
    except Exception as exc:
        return f"Search error: {exc}"


async def poly_image_gen(session, prompt):
    seed = random.randint(1, 100000)
    image_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={seed}"
    async with session.get(image_url) as response:
        response.raise_for_status()
        image_data = await response.read()
        return io.BytesIO(image_data)


async def generate_image_prodia(prompt, model, sampler, seed, neg):
    print("\\033[1;32m(Prodia) Creating image for :\\033[0m", prompt)
    start_time = time.time()
    if seed is None:
        seed = random.randint(1, 2_147_483_647)

    async def create_job():
        url = "https://api.prodia.com/generate"
        params = {
            "new": "true",
            "prompt": quote(prompt),
            "model": model,
            "steps": "100",
            "cfg": "9.5",
            "seed": str(seed),
            "sampler": sampler,
            "upscale": "True",
            "aspect_ratio": "square",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data["job"]

    job_id = await create_job()
    url = f"https://api.prodia.com/job/{job_id}"
    headers = {"accept": "*/*"}

    async with aiohttp.ClientSession() as session:
        for _ in range(180):
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                status_data = await response.json()
            if status_data.get("status") == "succeeded":
                async with session.get(f"https://images.prodia.xyz/{job_id}.png?download=1", headers=headers) as response:
                    response.raise_for_status()
                    content = await response.read()
                duration = time.time() - start_time
                print(f"\\033[1;34m(Prodia) Finished image creation\\n\\033[0mJob id : {job_id} Prompt : {prompt} in {duration:.1f} seconds.")
                return io.BytesIO(content)
            if status_data.get("status") in {"failed", "error"}:
                raise RuntimeError(f"Prodia job failed: {status_data}")
            await asyncio.sleep(1)
    raise TimeoutError("Prodia image generation timed out after 180 seconds")


async def text_to_speech(text):
    bytes_obj = io.BytesIO()
    detected_language = detect(text)
    tts = gTTS(text=text, lang=detected_language)
    tts.write_to_fp(bytes_obj)
    bytes_obj.seek(0)
    return bytes_obj
