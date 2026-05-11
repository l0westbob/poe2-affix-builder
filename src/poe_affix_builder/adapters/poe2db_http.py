from __future__ import annotations

import time
from typing import Callable

import httpx

DEFAULT_INDEX_URL = "https://poe2db.tw/us/Modifiers"
DEFAULT_HEADERS = {
    "User-Agent": "poe-affix-builder/0.1 (+https://example.invalid)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526, 527, 530}


def fetch_html_with_client(
    client: httpx.Client,
    url: str,
    *,
    max_attempts: int = 5,
    backoff_s: float = 1.0,
    emit: Callable[[str], None] | None = None,
) -> str:
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.get(url)
        except (httpx.TimeoutException, httpx.TransportError) as err:
            last_err = err
            if attempt >= max_attempts:
                break
            wait_s = backoff_s * (2 ** (attempt - 1))
            if emit is not None:
                emit(f"[poe2db] retry {attempt}/{max_attempts - 1} after transport error for {url}: {err} (sleep {wait_s:.1f}s)")
            time.sleep(wait_s)
            continue

        if resp.status_code >= 400:
            err = httpx.HTTPStatusError(
                f"HTTP {resp.status_code} for url {url}",
                request=resp.request,
                response=resp,
            )
            last_err = err
            if is_retryable_status(resp.status_code) and attempt < max_attempts:
                wait_s = backoff_s * (2 ** (attempt - 1))
                if emit is not None:
                    emit(f"[poe2db] retry {attempt}/{max_attempts - 1} after HTTP {resp.status_code} for {url} (sleep {wait_s:.1f}s)")
                time.sleep(wait_s)
                continue
            resp.raise_for_status()

        return resp.text

    if last_err is not None:
        raise RuntimeError(f"Failed fetching {url} after {max_attempts} attempts: {last_err}") from last_err
    raise RuntimeError(f"Failed fetching {url} after {max_attempts} attempts")


def fetch_html(
    url: str,
    *,
    timeout_s: float = 30.0,
    max_attempts: int = 5,
    backoff_s: float = 1.0,
    emit: Callable[[str], None] | None = None,
) -> str:
    with httpx.Client(follow_redirects=True, timeout=timeout_s, headers=DEFAULT_HEADERS) as client:
        return fetch_html_with_client(client, url, max_attempts=max_attempts, backoff_s=backoff_s, emit=emit)
