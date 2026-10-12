#!/usr/bin/env python3
"""Resolve every applied remote patch from its current upstream source."""
from __future__ import annotations

import argparse
import html
import hashlib
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Iterable

API = "https://api.github.com"
UA = "linux-charcoal-vulcano-dynamic-resolver/7"


class ResolveError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    path: str
    sha: str
    url: str
    compatibility: int
    kernel_version: tuple[int, ...] | None
    project_version: str | None


_TREE_CACHE: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}


def read_response(request: urllib.request.Request, timeout: int) -> bytes:
    """Retry transient transport failures while keeping the exact pinned URL."""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, ConnectionError, TimeoutError,
                http.client.IncompleteRead, http.client.RemoteDisconnected) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in {
                408, 429, 500, 502, 503, 504,
            }:
                raise
            if attempt == 3:
                raise
            delay = 2 ** attempt
            print(
                f"retrying {request.full_url} in {delay}s "
                f"after a transient network failure (attempt {attempt + 2}/4)",
                file=sys.stderr,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")


def request_json(url: str, token: str | None = None) -> Any:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": UA}
    if token:
        headers |= {
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    try:
        return json.loads(read_response(urllib.request.Request(url, headers=headers), 45))
    except (urllib.error.URLError, ConnectionError, TimeoutError,
            http.client.IncompleteRead, json.JSONDecodeError) as exc:
        raise ResolveError(f"unable to read {url}: {exc}") from exc


def request_bytes(url: str, token: str | None = None) -> bytes:
    headers = {"User-Agent": UA}
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    try:
        return read_response(urllib.request.Request(url, headers=headers), 90)
    except (urllib.error.URLError, ConnectionError, TimeoutError,
            http.client.IncompleteRead) as exc:
        raise ResolveError(f"unable to download {url}: {exc}") from exc


def version_key(text: str | None) -> tuple[int, ...]:
    values = [int(value) for value in re.findall(r"\d+", text or "")]
    return tuple(values[-8:]) if values else (0,)


def project_version_key(text: str | None) -> tuple[int, ...]:
    """Sort project releases semantically, including rc/pre and rN revisions."""
    raw = (text or "").strip().lower().lstrip("v")
    match = re.fullmatch(r"(?P<core>\d+(?:\.\d+)*)(?P<suffix>.*)", raw)
    if not match:
        return (0,) * 10

    core = [int(value) for value in match.group("core").split(".")]
    core = (core + [0] * 8)[:8]
    suffix = match.group("suffix")
    prerelease = re.search(r"(?:^|[-_.]?)(alpha|beta|pre|rc)(\d*)", suffix)
    postrelease = re.search(r"(?:^|[-_.]?)r(\d+)$", suffix)
    if prerelease:
        stage_rank = {"alpha": 0, "beta": 1, "pre": 2, "rc": 3}
        stage = stage_rank[prerelease.group(1)]
        serial = int(prerelease.group(2) or 0)
    elif postrelease:
        stage = 5
        serial = int(postrelease.group(1))
    else:
        stage = 4
        serial = 0
    return tuple(core + [stage, serial])


def parse_kernel_version(text: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    return (
        tuple(int(value) for value in match.groups() if value is not None)
        if match
        else None
    )


def regex_value(spec: dict[str, Any], key: str, path: str, group: str) -> str | None:
    expression = spec.get(key)
    if not expression:
        return None
    match = re.search(str(expression), path)
    if not match:
        return None
    return match.groupdict().get(group) or match.group(1)


def candidate_kernel_version(spec: dict[str, Any], path: str) -> tuple[int, ...] | None:
    raw = regex_value(spec, "kernel_version_regex", path, "kernel")
    return parse_kernel_version(raw) if raw else None


def candidate_project_version(spec: dict[str, Any], path: str) -> str | None:
    return regex_value(spec, "project_version_regex", path, "version")


def compatible_key(candidate: Candidate) -> tuple[Any, ...]:
    return (
        candidate.compatibility,
        project_version_key(candidate.project_version)
        if candidate.project_version
        else version_key(candidate.path),
        candidate.kernel_version or (0,),
        candidate.path,
    )


def latest_key(candidate: Candidate) -> tuple[Any, ...]:
    return (
        project_version_key(candidate.project_version)
        if candidate.project_version
        else version_key(candidate.path),
        candidate.kernel_version or (0,),
        candidate.path,
    )


def latest_project_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Keep every kernel variant of the newest project release.

    Kernel compatibility must never make an older project release win. Once the
    newest project release is known, prefer a matching kernel variant FROM
    THAT RELEASE. Port the nearest kernel variant only if that release has
    no native variant. Never replace newer functional code with an older native patch.
    """
    versioned = [item for item in candidates if item.project_version]
    if not versioned:
        return candidates
    latest = max(project_version_key(item.project_version) for item in versioned)
    return [
        item
        for item in versioned
        if project_version_key(item.project_version) == latest
    ]


def project_base_version_key(value: str | None) -> tuple[int, ...]:
    """Compare numeric upstream versions separately from their rN/RC variants."""
    match = re.match(r"^v?(\d+(?:\.\d+)*)", (value or "").strip().lower())
    if match is None:
        return ()
    parts = [int(part) for part in match.group(1).split(".")]
    return tuple((parts + [0] * 8)[:8])


def latest_base_release_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Collect every kernel variant of the latest numeric upstream release.

    A newer numeric release (NAP 0.6.5 vs 0.5.1) always wins. A suffix rN
    revises that release; when the same base is available natively, prefer its
    kernel-specific source before attempting to port the foreign rN revision.
    """
    versioned = [item for item in candidates if item.project_version]
    if not versioned:
        return candidates
    newest = max(project_base_version_key(item.project_version) for item in versioned)
    return [item for item in versioned if project_base_version_key(item.project_version) == newest]


def nearest_candidate(candidates: list[Candidate], kernel_version: str) -> Candidate | None:
    target = parse_kernel_version(kernel_version)
    if target is None:
        raise ResolveError(f"invalid kernel version: {kernel_version}")

    def distance(candidate: Candidate) -> int:
        version = candidate.kernel_version or ()
        left = version + (0,) * (3 - len(version))
        right = target + (0,) * (3 - len(target))
        return (
            abs(left[0] - right[0]) * 1_000_000
            + abs(left[1] - right[1]) * 1_000
            + abs(left[2] - right[2])
        )

    versioned = [item for item in candidates if item.kernel_version]
    if not versioned:
        return None
    minimum = min(distance(item) for item in versioned)
    return max((item for item in versioned if distance(item) == minimum), key=latest_key)


def native_series_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Return candidates built for the target kernel series.

    ``upstream_candidates()`` assigns compatibility 2 to same-major/minor
    variants and 3 to an exact patch-level match.  Keeping this decision in a
    named helper makes the policy explicit: the newest upstream project
    release is selected first, then its native kernel-series variant is preferred over
    every local port.
    """
    return [item for item in candidates if item.compatibility >= 2]


def fallback_metadata(
    spec: dict[str, Any], kernel_version: str
) -> dict[str, Any] | None:
    """Describe the reviewed port that may be used after a real apply failure.

    The resolver must never replace a newest native 6.18 patch with a local
    port merely because a port exists.  The build-time applicator uses this
    metadata only after it has proved that the selected upstream bytes do not
    apply to the selected Valve source tree.
    """
    local_port = spec.get("local_port")
    adaptive_port = spec.get("adaptive_port")
    if local_port and adaptive_port:
        raise ResolveError(
            f"{spec['name']}: local_port and adaptive_port are mutually exclusive"
        )
    if local_port:
        result: dict[str, Any] = {
            "kind": "local-port",
            "path": str(local_port),
            # The port policy may cover the whole 6.18 series, but this lock
            # describes one exact Valve source tree.  Keep the latter here so
            # the applicator cannot reuse a fallback from another build.
            "kernel_version": kernel_version,
        }
        for manifest_key, lock_key in (
            ("local_port_project_version", "project_version"),
            ("local_port_upstream_sha256", "upstream_sha256"),
        ):
            value = spec.get(manifest_key)
            if value is not None:
                result[lock_key] = str(value)
        return result
    if adaptive_port:
        return {
            "kind": "adaptive-port",
            "adapter": str(adaptive_port),
            "kernel_version": kernel_version,
        }
    return None


def paged(url: str, token: str | None) -> Iterable[Any]:
    page = 1
    while True:
        separator = "&" if "?" in url else "?"
        data = request_json(f"{url}{separator}per_page=100&page={page}", token)
        if not isinstance(data, list):
            raise ResolveError(f"expected a list from {url}")
        yield from data
        if len(data) < 100:
            return
        page += 1


def kernel_matches_policy(version: str, config: dict[str, Any]) -> bool:
    """Return whether a Valve kernel version belongs to the configured target."""
    required = config.get("version")
    if required:
        return version == str(required)

    series = config.get("series")
    if not series:
        return True
    target = parse_kernel_version(str(series))
    candidate = parse_kernel_version(version)
    return bool(target and candidate and candidate[: len(target)] == target)


def resolve_official_kernel_package(
    config: dict[str, Any], token: str | None
) -> dict[str, Any] | None:
    """Resolve the newest source package in Valve's public SteamOS index.

    The GitHub mirror is convenient for git checkout, but it is not the
    authority for which SteamOS release is published.  When the manifest
    enables this check, only a mirror tag that exactly corresponds to the
    newest source package in the official index can be selected.
    """
    index_url = config.get("official_source_index")
    package_regex = config.get("official_package_regex")
    if not index_url and not package_regex:
        return None
    if not isinstance(index_url, str) or not isinstance(package_regex, str):
        raise ResolveError(
            "kernel source must declare both official_source_index and "
            "official_package_regex"
        )

    try:
        listing = request_bytes(index_url, token).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ResolveError(f"official SteamOS source index is not UTF-8: {index_url}") from exc

    pattern = re.compile(package_regex)
    filenames = {
        html.unescape(value).rsplit("/", 1)[-1]
        for value in re.findall(r'''(?i)href=["']([^"']+)["']''', listing)
    }
    matches: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for filename in filenames:
        match = pattern.fullmatch(filename)
        if not match:
            continue
        version = match.group("version")
        valve = match.group("valve")
        pkgrel = match.groupdict().get("pkgrel", "0")
        if not kernel_matches_policy(version, config):
            continue
        try:
            pkgrel_key = int(pkgrel)
        except ValueError as exc:
            raise ResolveError(
                f"invalid pkgrel {pkgrel!r} in official SteamOS package {filename}"
            ) from exc
        matches.append(
            (
                (version_key(version), version_key(valve), pkgrel_key, filename),
                {
                    "filename": filename,
                    "url": urllib.parse.urljoin(index_url, filename),
                    "tag": f"{version}-valve{valve}",
                    "version": version,
                    "valve": valve,
                    "pkgrel": pkgrel_key,
                },
            )
        )
    if not matches:
        target = config.get("series") or config.get("version") or "configured"
        raise ResolveError(
            f"no official SteamOS source package matched kernel target {target!r}"
        )
    return max(matches, key=lambda item: item[0])[1]


def resolve_kernel_tag(
    config: dict[str, Any], token: str | None
) -> tuple[str, str, dict[str, Any] | None]:
    pattern = re.compile(config["tag_regex"])
    required = config.get("version")
    series = config.get("series")
    prefix_source = required or series
    official_package = resolve_official_kernel_package(config, token)
    if prefix_source:
        prefix = urllib.parse.quote(str(prefix_source), safe="")
        tags: Iterable[Any] = request_json(
            f"{API}/repos/{config['repository']}/git/matching-refs/tags/{prefix}", token
        )
        if not isinstance(tags, list):
            raise ResolveError("expected a list from matching tag refs")
    else:
        tags = paged(f"{API}/repos/{config['repository']}/tags", token)

    matches: list[tuple[tuple[int, ...], str, str, str | None]] = []
    for item in tags:
        annotated_url = None
        if "ref" in item:
            name = str(item["ref"]).removeprefix("refs/tags/")
            obj = item.get("object", {})
            sha = obj.get("sha")
            annotated_url = obj.get("url") if obj.get("type") == "tag" else None
        else:
            name = item.get("name", "")
            sha = item.get("commit", {}).get("sha")
        match = pattern.fullmatch(name)
        if not match or "-rc" in name.lower():
            continue
        if not kernel_matches_policy(match.group("version"), config):
            continue
        if official_package and name != official_package["tag"]:
            continue
        if sha:
            score = version_key(match.group("version")) + version_key(match.group("valve"))
            matches.append((score, name, sha, annotated_url))
    if not matches:
        if official_package:
            raise ResolveError(
                "the official SteamOS source package "
                f"{official_package['filename']} requires mirror tag "
                f"{official_package['tag']}, but it is unavailable"
            )
        target = config.get("series") or config.get("version") or "configured"
        raise ResolveError(f"no Valve SteamOS tag matched kernel target {target!r}")
    _, name, sha, annotated_url = max(matches)
    if annotated_url:
        sha = request_json(annotated_url, token).get("object", {}).get("sha", sha)
    return name, sha, official_package


def repository_tree(repo: str, branch: str, token: str | None) -> tuple[str, dict[str, Any]]:
    key = (repo, branch)
    if key not in _TREE_CACHE:
        encoded = urllib.parse.quote(branch, safe="")
        branch_data = request_json(f"{API}/repos/{repo}/branches/{encoded}", token)
        commit = branch_data["commit"]["sha"]
        tree = request_json(f"{API}/repos/{repo}/git/trees/{commit}?recursive=1", token)
        if tree.get("truncated"):
            raise ResolveError(
                f"GitHub tree for {repo}@{branch} was truncated; refusing a partial search"
            )
        _TREE_CACHE[key] = commit, tree
    return _TREE_CACHE[key]


def upstream_candidates(
    spec: dict[str, Any], kernel_version: str, token: str | None
) -> list[Candidate]:
    repo = spec["repository"]
    commit, tree = repository_tree(repo, spec.get("ref", "main"), token)
    include = re.compile(spec["filename_regex"])
    exclude = re.compile(spec["exclude_regex"]) if spec.get("exclude_regex") else None
    target = parse_kernel_version(kernel_version)
    if target is None:
        raise ResolveError(f"invalid kernel version: {kernel_version}")
    result: list[Candidate] = []
    for item in tree.get("tree", []):
        path = item.get("path", "")
        if item.get("type") != "blob" or not include.match(path):
            continue
        if exclude and exclude.search(path):
            continue
        kernel = candidate_kernel_version(spec, path)
        compatibility = (
            3
            if kernel == target
            else 2
            if kernel and kernel[:2] == target[:2]
            else 0
        )
        result.append(
            Candidate(
                path,
                commit,
                f"https://raw.githubusercontent.com/{repo}/{commit}/{path}",
                compatibility,
                kernel,
                candidate_project_version(spec, path),
            )
        )
    return result


def looks_like_patch(data: bytes) -> bool:
    return bool(data) and data.startswith(
        (b"From ", b"From:", b"diff --git", b"--- ", b"---\n")
    )


def decode_mailbox_patch(data: bytes) -> bytes:
    """Extract the patch payload from a MIME-encoded mailing-list message."""
    message = BytesParser(policy=policy.default).parsebytes(data)
    part = message.get_body(preferencelist=("plain",)) or message
    payload = part.get_payload(decode=True)
    if payload is None:
        content = part.get_content()
        if isinstance(content, bytes):
            payload = content
        elif isinstance(content, str):
            payload = content.encode(part.get_content_charset() or "utf-8")
        else:
            raise ResolveError("mailbox body is not text")

    payload = payload.replace(b"\r\n", b"\n")
    if payload.startswith(b"---\n"):
        patch = payload
    else:
        separator = payload.find(b"\n---\n")
        if separator < 0:
            raise ResolveError("mailbox body does not contain a patch separator")
        patch = payload[separator + 1 :]

    trailer = patch.find(b"\n-- \n")
    if trailer >= 0:
        patch = patch[:trailer]
    if not looks_like_patch(patch):
        raise ResolveError("decoded mailbox body is not a patch")
    return patch


def resolve_github_component(
    spec: dict[str, Any], kernel_version: str, token: str | None, root: Path
) -> dict[str, Any]:
    all_candidates = upstream_candidates(spec, kernel_version, token)
    if not all_candidates:
        raise ResolveError(f"no official upstream patch found for {spec['name']}")

    # 1. Discover newest numeric project release across stable/testing/RC/rN.
    # 2. Within that release prefer the latest native kernel-series variant.
    # 3. Otherwise choose latest suffix/revision and nearest porting base.
    # A 0.12.0r2 7.3 patch must not hide an existing 0.12.0 6.18 patch;
    # but a native 0.5.1 cannot replace a newer numeric NAP 0.6.5.
    latest_family = latest_base_release_candidates(all_candidates)
    native_family = native_series_candidates(latest_family)
    candidates = latest_project_candidates(native_family or latest_family)
    native = native_series_candidates(candidates)
    compatibility_reference = native_series_candidates(all_candidates)
    local_port = spec.get("local_port")
    adaptive_port = spec.get("adaptive_port")
    use_local_port = False
    use_adaptive_port = False

    if native:
        # This is deliberately ahead of every port branch. A port is a
        # fallback for an unavailable or non-applying 6.18 variant, never a
        # substitute for an official native variant of the latest project release.
        candidate = max(native, key=compatible_key)
        selection = "latest-native-series"
    elif not any(item.kernel_version for item in candidates):
        # Some upstreams publish a single, kernel-agnostic patch. It has no
        # versioned 6.18 sibling to choose from, so retain the newest official
        # source and let the source-tree application preflight validate it.
        candidate = max(candidates, key=latest_key)
        selection = "latest-kernel-agnostic"
    else:
        candidate = nearest_candidate(candidates, kernel_version) or max(
            candidates, key=latest_key
        )
        if (
            not candidate
            or not (local_port or adaptive_port)
            or not spec.get("port_when_incompatible", True)
        ):
            raise ResolveError(
                f"no native {kernel_version.rsplit('.', 1)[0]} patch exists for "
                f"the newest upstream release of {spec['name']}; a tracked port is required"
            )
        use_local_port = bool(local_port)
        use_adaptive_port = bool(adaptive_port)
        selection = "latest-release-port" if use_local_port else "latest-release-adaptive-port"

    upstream: dict[str, Any] = {
        "repository": spec["repository"],
        "path": candidate.path,
        "commit": candidate.sha,
        "url": candidate.url,
        "selection": selection,
    }
    if candidate.kernel_version:
        upstream["kernel_version"] = ".".join(map(str, candidate.kernel_version))
    if candidate.project_version:
        upstream["project_version"] = candidate.project_version
        newest_upstream = latest_project_candidates(all_candidates)
        latest_version = max(newest_upstream, key=latest_key).project_version
        if latest_version:
            upstream["latest_upstream_project_version"] = latest_version

    # Keep the best direct-compatible baseline visible in the lock for audit
    # purposes when a newer release is being sourced from another kernel base.
    if compatibility_reference:
        reference = max(compatibility_reference, key=compatible_key)
        if reference.path != candidate.path:
            upstream["compatibility_reference"] = {
                "path": reference.path,
                "kernel_version": ".".join(map(str, reference.kernel_version or ())),
                "project_version": reference.project_version,
            }

    if not use_local_port and not use_adaptive_port:
        result = {
            **upstream,
            "origin": "upstream-native" if native else "upstream-kernel-agnostic",
        }
        fallback = fallback_metadata(spec, kernel_version)
        if fallback:
            result["fallback"] = fallback
        return result

    official = request_bytes(candidate.url, token)
    if not looks_like_patch(official):
        raise ResolveError(f"selected upstream source is not a patch: {candidate.url}")

    if use_adaptive_port:
        return {
            **upstream,
            "origin": "adaptive-port",
            "adapter": str(adaptive_port),
            "content_bytes": official,
        }

    path = root / str(local_port)
    base_data = path.read_bytes() if path.is_file() else b""
    if not base_data or not looks_like_patch(base_data):
        raise ResolveError(f"local port is missing or invalid: {local_port}")
    official_sha = hashlib.sha256(official).hexdigest()
    expected = spec.get("local_port_upstream_sha256")
    if not expected:
        raise ResolveError(
            f"local port for {spec['name']} must declare local_port_upstream_sha256 "
            "to track the exact newest upstream bytes"
        )
    if official_sha != expected:
        raise ResolveError(
            f"local port for {spec['name']} follows upstream SHA-256 {expected}, "
            f"but current upstream is {official_sha}; refresh and validate the port"
        )

    expected_project_version = spec.get("local_port_project_version")
    if candidate.project_version:
        if expected_project_version is None:
            raise ResolveError(
                f"local port for {spec['name']} must declare "
                "local_port_project_version to track the selected upstream release"
            )
        if str(expected_project_version) != candidate.project_version:
            raise ResolveError(
                f"local port for {spec['name']} implements project version "
                f"{expected_project_version}, but the selected closest upstream "
                f"source is {candidate.project_version}; refresh and validate the port"
            )
    data = base_data
    overlay_records: list[dict[str, Any]] = []
    for overlay_value in spec.get("local_port_overlays", []):
        overlay_path = root / str(overlay_value)
        overlay_data = overlay_path.read_bytes() if overlay_path.is_file() else b""
        if not overlay_data or not looks_like_patch(overlay_data):
            raise ResolveError(f"local port overlay is missing or invalid: {overlay_value}")
        diff_start = overlay_data.find(b"diff --git ")
        if diff_start < 0:
            raise ResolveError(f"local port overlay has no unified diff: {overlay_value}")
        if not data.endswith(b"\n"):
            data += b"\n"
        data += overlay_data[diff_start:]
        overlay_records.append(
            {
                "path": str(overlay_value),
                "sha256": hashlib.sha256(overlay_data).hexdigest(),
                "size": len(overlay_data),
            }
        )

    upstream |= {"sha256": official_sha, "size": len(official)}
    return {
        "repository": "zarpon/linux-charcoal-vulcano",
        "path": str(local_port),
        "commit": "repository-local",
        "url": None,
        "origin": "local-port",
        "selection": selection,
        "upstream": upstream,
        "local_port_overlays": overlay_records,
        "content_bytes": data,
    }


def resolve_http_component(
    spec: dict[str, Any], kernel_version: str, token: str | None, root: Path
) -> dict[str, Any]:
    series = ".".join(kernel_version.split(".")[:2])
    errors: list[str] = []
    for template in spec.get("urls", []):
        url = str(template).format(kernel_version=kernel_version, series=series)
        try:
            data = request_bytes(url, token)
            if spec.get("mailbox"):
                data = decode_mailbox_patch(data)
            if not looks_like_patch(data):
                raise ResolveError("response is not a patch")
            upstream = {
                "repository": spec.get("repository", url),
                "path": spec.get("path"),
                "commit": spec.get("commit"),
                "url": url,
                "selection": "first-valid",
            }
            local_port = spec.get("local_port")
            if local_port:
                path = root / str(local_port)
                local_data = path.read_bytes() if path.is_file() else b""
                if not local_data or not looks_like_patch(local_data):
                    raise ResolveError(f"local port is missing or invalid: {local_port}")

                official_sha = hashlib.sha256(data).hexdigest()
                expected_sha = spec.get("local_port_upstream_sha256")
                if not expected_sha:
                    raise ResolveError(
                        f"unversioned local port for {spec['name']} must declare "
                        "local_port_upstream_sha256"
                    )
                if official_sha != expected_sha:
                    raise ResolveError(
                        f"local port for {spec['name']} follows upstream SHA-256 "
                        f"{expected_sha}, but current upstream is {official_sha}; "
                        "refresh and validate the port"
                    )

                fallback = fallback_metadata(spec, kernel_version)
                if fallback is None:
                    raise ResolveError(
                        f"local port for {spec['name']} has no fallback metadata"
                    )
                upstream["fallback"] = fallback

            return {
                **upstream,
                "origin": "upstream-fixed",
                "content_bytes": data,
            }
        except ResolveError as exc:
            errors.append(f"{url}: {exc}")
    raise ResolveError(f"no usable URL for {spec['name']}: {' | '.join(errors)}")


def resolve_component(
    spec: dict[str, Any], kernel_version: str, token: str | None, root: Path
) -> dict[str, Any]:
    kind = spec.get("kind", "github_tree")
    if kind == "github_tree":
        return resolve_github_component(spec, kernel_version, token, root)
    if kind == "http_patch":
        return resolve_http_component(spec, kernel_version, token, root)
    raise ResolveError(f"unknown component kind {kind!r} for {spec['name']}")


def replace_assignment(text: str, variable: str, value: str) -> str:
    updated, count = re.subn(
        rf"(?m)^{re.escape(variable)}=.*$", f"{variable}={value}", text, count=1
    )
    if count != 1:
        raise ResolveError(f"assignment {variable} not found in PKGBUILD")
    return updated


def find_array_bounds(text: str, variable: str) -> tuple[int, int]:
    start = re.search(rf"(?m)^{re.escape(variable)}=\(", text)
    if not start:
        raise ResolveError(f"{variable} array not found")
    end = re.search(r"(?m)^\s*\)\s*$", text[start.end() :])
    if not end:
        raise ResolveError(f"unterminated {variable} array")
    return start.start(), start.end() + end.end()


def normalized_source_line(line: str) -> str:
    value = line.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def replace_source_entries(
    text: str, components: list[dict[str, Any]], replacements: dict[str, str]
) -> str:
    start, end = find_array_bounds(text, "source")
    lines = text[start:end].splitlines(keepends=True)
    for spec in components:
        target = replacements[spec["name"]]
        if any(normalized_source_line(line) == target for line in lines):
            continue
        matches = [
            index
            for index, line in enumerate(lines)
            if re.fullmatch(str(spec["source_regex"]), normalized_source_line(line))
        ]
        if len(matches) != 1:
            raise ResolveError(
                f"source entry for {spec['name']}: expected one match, found {len(matches)}"
            )
        newline = "\n" if lines[matches[0]].endswith("\n") else ""
        lines[matches[0]] = f"  {target}{newline}"
    return text[:start] + "".join(lines) + text[end:]


def replace_sha_array_with_skip(text: str) -> str:
    source_start, source_end = find_array_bounds(text, "source")
    count = sum(
        1
        for line in text[source_start:source_end].splitlines()[1:-1]
        if line.strip() and not line.lstrip().startswith("#")
    )
    sha_start, sha_end = find_array_bounds(text, "sha256sums")
    array = "sha256sums=(\n" + "\n".join("  'SKIP'" for _ in range(count)) + "\n)"
    return text[:sha_start] + array + text[sha_end:]


def validate_manifest(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if manifest.get("schema") != 4:
        raise ResolveError("unsupported patch source manifest schema")
    kernel_source = manifest.get("kernel_source")
    if not isinstance(kernel_source, dict):
        raise ResolveError("kernel_source must be an object")
    if not isinstance(kernel_source.get("repository"), str) or not isinstance(
        kernel_source.get("tag_regex"), str
    ):
        raise ResolveError("kernel_source requires repository and tag_regex")
    if kernel_source.get("version") and kernel_source.get("series"):
        raise ResolveError("kernel_source cannot declare both version and series")
    if not kernel_source.get("version") and not kernel_source.get("series"):
        raise ResolveError("kernel_source requires version or series")
    target = str(kernel_source.get("version") or kernel_source.get("series"))
    if parse_kernel_version(target) is None:
        raise ResolveError(f"kernel_source target is invalid: {target!r}")
    index = kernel_source.get("official_source_index")
    package_regex = kernel_source.get("official_package_regex")
    if bool(index) != bool(package_regex):
        raise ResolveError(
            "kernel_source official_source_index and official_package_regex must be declared together"
        )
    if index and (not isinstance(index, str) or not isinstance(package_regex, str)):
        raise ResolveError("kernel_source official source settings must be strings")
    groups = {
        "components": list(manifest.get("components", [])),
        "auxiliary_components": list(manifest.get("auxiliary_components", [])),
    }
    all_components = groups["components"] + groups["auxiliary_components"]
    names = [str(item.get("name", "")) for item in all_components]
    targets = [str(item.get("target", "")) for item in all_components]
    if not names or any(not name for name in names) or len(set(names)) != len(names):
        raise ResolveError("patch component names must be non-empty and unique")
    if any(not target for target in targets) or len(set(targets)) != len(targets):
        raise ResolveError("patch component targets must be non-empty and unique")
    if any(not item.get("source_regex") for item in all_components):
        raise ResolveError("every patch component requires source_regex")
    for item in all_components:
        local_port = item.get("local_port")
        adaptive_port = item.get("adaptive_port")
        kind = item.get("kind", "github_tree")
        if local_port and adaptive_port:
            raise ResolveError(
                f"{item['name']}: local_port and adaptive_port are mutually exclusive"
            )
        if (local_port or adaptive_port) and not isinstance(
            item.get("port_for_kernel"), str
        ):
            raise ResolveError(
                f"{item['name']}: every reviewed port requires port_for_kernel"
            )
        if item.get("mailbox") and kind != "http_patch":
            raise ResolveError(f"{item['name']}: mailbox decoding requires http_patch")
        if kind == "http_patch" and local_port and not item.get(
            "local_port_upstream_sha256"
        ):
            raise ResolveError(
                f"{item['name']}: local http port requires local_port_upstream_sha256"
            )
        if adaptive_port and (
            kind != "github_tree"
            or not isinstance(adaptive_port, str)
            or not adaptive_port
        ):
            raise ResolveError(
                f"{item['name']}: adaptive_port requires a non-empty github_tree adapter name"
            )
    return groups


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="automation/patch-sources.json")
    parser.add_argument("--overrides", default="automation/patch-source-overrides.json")
    parser.add_argument("--pkgbuild", default="PKGBUILD")
    parser.add_argument("--lock", default="logs/patch-lock.json")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--fixture")
    args = parser.parse_args()

    root = Path.cwd()
    manifest = json.loads((root / args.manifest).read_text(encoding="utf-8"))
    override_path = root / args.overrides
    if override_path.is_file():
        overrides = json.loads(override_path.read_text(encoding="utf-8"))
        if overrides.get("schema") != 1:
            raise ResolveError("unsupported patch source override schema")
        for group_name in ("components", "auxiliary_components"):
            configured = overrides.get(group_name, {})
            if not isinstance(configured, dict):
                raise ResolveError(f"override group {group_name!r} must be an object")
            by_name = {
                str(item.get("name", "")): item
                for item in manifest.get(group_name, [])
                if isinstance(item, dict)
            }
            for name, values in configured.items():
                if name not in by_name or not isinstance(values, dict):
                    raise ResolveError(f"invalid override for {group_name}.{name}")
                by_name[name].update(values)
    groups = validate_manifest(manifest)
    all_components = groups["components"] + groups["auxiliary_components"]
    pkgbuild_path = root / args.pkgbuild
    pkgbuild = pkgbuild_path.read_text(encoding="utf-8")
    token = os.environ.get("GITHUB_TOKEN")

    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        kernel_tag = fixture["kernel_tag"]
        kernel_sha = fixture.get("kernel_sha", "fixture")
        selected_groups = {
            name: fixture.get(name, {}) for name in ("components", "auxiliary_components")
        }
    else:
        kernel_tag, kernel_sha, official_kernel = resolve_kernel_tag(
            manifest["kernel_source"], token
        )
        kernel_version = kernel_tag.split("-valve", 1)[0]
        selected_groups = {
            name: {
                spec["name"]: resolve_component(spec, kernel_version, token, root)
                for spec in specs
            }
            for name, specs in groups.items()
        }

    if args.fixture:
        official_kernel = fixture.get("official_kernel")

    kernel_version = kernel_tag.split("-valve", 1)[0]
    kernel_record: dict[str, Any] = {
        "tag": kernel_tag,
        "version": kernel_version,
        "commit": kernel_sha,
    }
    if official_kernel is not None:
        if not isinstance(official_kernel, dict):
            raise ResolveError("fixture official_kernel must be an object")
        kernel_record["official_source_package"] = official_kernel
    lock: dict[str, Any] = {
        "schema": 5,
        "kernel": kernel_record,
        "components": {},
        "auxiliary_components": {},
    }
    replacements: dict[str, str] = {}
    for group_name, specs in groups.items():
        selected = selected_groups[group_name]
        for spec in specs:
            name, target, item = spec["name"], spec["target"], selected[spec["name"]]
            if "content_bytes" in item:
                data = item["content_bytes"]
            elif args.fixture:
                data = item.get("content", "fixture patch\n").encode()
            elif item.get("origin") == "local-port":
                data = (root / item["path"]).read_bytes()
            else:
                data = request_bytes(item["url"], token)
            if not (looks_like_patch(data) or data.startswith(b"fixture")):
                raise ResolveError(f"patch for {name} does not look valid")
            clean = {
                key: value
                for key, value in item.items()
                if key not in {"content_bytes", "content"}
            }
            lock[group_name][name] = {
                **clean,
                "target": target,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
            replacements[name] = target
            if args.write:
                (root / target).write_bytes(data)

    updated = replace_assignment(pkgbuild, "_tag", kernel_tag)
    updated = replace_source_entries(updated, all_components, replacements)
    updated = replace_sha_array_with_skip(updated)
    if args.write:
        pkgbuild_path.write_text(updated, encoding="utf-8")

    lock_path = root / args.lock
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ResolveError as exc:
        print(f"resolver error: {exc}", file=sys.stderr)
        raise SystemExit(2)
