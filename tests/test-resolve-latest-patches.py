#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "automation/resolve-latest-patches.py"
SPEC = importlib.util.spec_from_file_location("charcoal_patch_resolver", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PATCH = b"From 1111111111111111111111111111111111111111 Mon Sep 17 00:00:00 2001\nSubject: [PATCH] demo\n\ndiff --git a/demo.c b/demo.c\n--- a/demo.c\n+++ b/demo.c\n@@ -1 +1 @@\n-old\n+new\n"
MBOX = (
    b"From nobody Tue Jul 28 07:31:55 2026\n"
    b"From: Example <example@example.invalid>\n"
    b"Subject: [PATCH] demo\n"
    b"MIME-Version: 1.0\n"
    b"Content-Type: text/plain; charset=UTF-8\n"
    b"Content-Transfer-Encoding: quoted-printable\n"
    b"\n"
    b"Demo patch body.\n"
    b"\n"
    b"---\n"
    b" demo.c | 2 +-\n"
    b" 1 file changed, 1 insertion(+), 1 deletion(-)\n"
    b"\n"
    b"diff --git a/demo.c b/demo.c\n"
    b"index 1111111..2222222 100644\n"
    b"--- a/demo.c\n"
    b"+++ b/demo.c\n"
    b"@@ -1 +1 @@\n"
    b"-old=3Dvalue\n"
    b"+new=3Dvalue\n"
    b"\n"
    b"-- \n"
    b"2.53.0\n"
)
DECODED_MBOX_PATCH = (
    b"---\n"
    b" demo.c | 2 +-\n"
    b" 1 file changed, 1 insertion(+), 1 deletion(-)\n"
    b"\n"
    b"diff --git a/demo.c b/demo.c\n"
    b"index 1111111..2222222 100644\n"
    b"--- a/demo.c\n"
    b"+++ b/demo.c\n"
    b"@@ -1 +1 @@\n"
    b"-old=value\n"
    b"+new=value\n"
)


class NetworkRetryTests(unittest.TestCase):
    @staticmethod
    def response(payload):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = payload
        return response

    def test_connection_reset_retries_the_same_pinned_patch(self):
        url = "https://raw.githubusercontent.com/example/patches/abcdef/demo.patch"
        with (
            mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=[
                MODULE.urllib.error.URLError(ConnectionResetError(104, "Connection reset by peer")),
                self.response(PATCH),
            ]) as open_url,
            mock.patch.object(MODULE.time, "sleep") as sleep,
        ):
            self.assertEqual(MODULE.request_bytes(url), PATCH)
        self.assertEqual(open_url.call_count, 2)
        self.assertEqual([call.args[0].full_url for call in open_url.call_args_list], [url, url])
        sleep.assert_called_once_with(1)

    def test_server_error_retries_json_and_preserves_authorization(self):
        url = MODULE.API + "/repos/example/patches/tags"
        with (
            mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=[
                MODULE.urllib.error.HTTPError(url, 503, "Unavailable", {}, None),
                self.response(b'[{"name":"v1"}]'),
            ]) as open_url,
            mock.patch.object(MODULE.time, "sleep"),
        ):
            self.assertEqual(MODULE.request_json(url, "test-token"), [{"name": "v1"}])
        for call in open_url.call_args_list:
            self.assertEqual(call.args[0].get_header("Authorization"), "Bearer test-token")

    def test_incomplete_download_is_discarded_before_retry(self):
        incomplete = self.response(b"")
        incomplete.read.side_effect = MODULE.http.client.IncompleteRead(b"partial", 100)
        with (
            mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=[incomplete, self.response(PATCH)]),
            mock.patch.object(MODULE.time, "sleep"),
        ):
            self.assertEqual(MODULE.request_bytes("https://example.invalid/demo.patch"), PATCH)
        incomplete.__exit__.assert_called_once()

    def test_persistent_network_failure_still_aborts_after_four_attempts(self):
        with (
            mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=TimeoutError("timed out")) as open_url,
            mock.patch.object(MODULE.time, "sleep") as sleep,
        ):
            with self.assertRaisesRegex(MODULE.ResolveError, "unable to download"):
                MODULE.request_bytes("https://example.invalid/demo.patch")
        self.assertEqual(open_url.call_count, 4)
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2), mock.call(4)])

    def test_permanent_http_errors_are_not_retried(self):
        url = "https://example.invalid/demo.patch"
        for status in (401, 403, 404):
            with (
                self.subTest(status=status),
                mock.patch.object(MODULE.urllib.request, "urlopen", side_effect=
                    MODULE.urllib.error.HTTPError(url, status, "Denied", {}, None)) as open_url,
                mock.patch.object(MODULE.time, "sleep") as sleep,
            ):
                with self.assertRaises(MODULE.ResolveError):
                    MODULE.request_bytes(url)
                open_url.assert_called_once()
                sleep.assert_not_called()


class LocalPortTrackingTests(unittest.TestCase):
    def candidate(
        self,
        version: str | None,
        *,
        kernel: tuple[int, ...] = (6, 16, 0),
        compatibility: int = 0,
    ) -> object:
        return MODULE.Candidate(
            path="patches/stable/0001-linux6.18-demo-2.0.patch",
            sha="a" * 40,
            url="https://example.invalid/demo.patch",
            compatibility=compatibility,
            kernel_version=kernel,
            project_version=version,
        )

    @staticmethod
    def base_spec() -> dict[str, object]:
        upstream_sha = hashlib.sha256(PATCH).hexdigest()
        return {
            "name": "demo",
            "repository": "example/demo",
            "local_port": "demo.patch",
            "port_for_kernel": "6.18.45",
            "port_when_incompatible": True,
            "local_port_project_version": "1.0",
            "local_port_upstream_sha256": upstream_sha,
        }

    def test_version_change_rejects_stale_local_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.patch").write_bytes(PATCH)
            with mock.patch.object(MODULE, "upstream_candidates", return_value=[self.candidate("2.0")]), mock.patch.object(MODULE, "request_bytes", return_value=PATCH):
                with self.assertRaisesRegex(MODULE.ResolveError, "selected closest upstream source is 2.0"):
                    MODULE.resolve_github_component(self.base_spec(), "6.18.45", None, root)

    def test_matching_version_accepts_tracked_local_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.patch").write_bytes(PATCH)
            spec = self.base_spec()
            spec["local_port_project_version"] = "2.0"
            with mock.patch.object(MODULE, "upstream_candidates", return_value=[self.candidate("2.0")]), mock.patch.object(MODULE, "request_bytes", return_value=PATCH):
                selected = MODULE.resolve_github_component(spec, "6.18.45", None, root)
        self.assertEqual(selected["origin"], "local-port")
        self.assertEqual(selected["upstream"]["project_version"], "2.0")

    def test_latest_native_series_patch_wins_over_a_local_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = self.base_spec()
            with mock.patch.object(
                MODULE,
                "upstream_candidates",
                return_value=[
                    self.candidate("2.0"),
                    self.candidate(
                        "2.0", kernel=(6, 18, 22), compatibility=2
                    ),
                ],
            ):
                selected = MODULE.resolve_github_component(
                    spec, "6.18.45", None, root
                )

        self.assertEqual(selected["origin"], "upstream-native")
        self.assertEqual(selected["selection"], "latest-native-series")
        self.assertEqual(selected["kernel_version"], "6.18.22")
        self.assertEqual(
            selected["fallback"],
            {
                "kind": "local-port",
                "path": "demo.patch",
                "kernel_version": "6.18.45",
                "project_version": "1.0",
                "upstream_sha256": hashlib.sha256(PATCH).hexdigest(),
            },
        )

    def test_series_port_locks_the_exact_resolved_valve_patchlevel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = self.base_spec()
            spec["port_for_kernel"] = "6.18"
            with mock.patch.object(
                MODULE,
                "upstream_candidates",
                return_value=[
                    self.candidate("2.0", kernel=(6, 18, 22), compatibility=2)
                ],
            ):
                selected = MODULE.resolve_github_component(
                    spec, "6.18.46", None, Path(tmp)
                )

        self.assertEqual(selected["fallback"]["kernel_version"], "6.18.46")

    def test_lru_marie_testing_0106_prefers_the_native_618_variant(self) -> None:
        candidates = [
            MODULE.Candidate(
                "patches/testing/0001-linux6.16.12-lru_marie-0.10.6.patch",
                "a" * 40,
                "https://example.invalid/lru-6.16.patch",
                0,
                (6, 16, 12),
                "0.10.6",
            ),
            MODULE.Candidate(
                "patches/testing/0001-linux6.18.22-lru_marie-0.10.6.patch",
                "b" * 40,
                "https://example.invalid/lru-6.18.patch",
                2,
                (6, 18, 22),
                "0.10.6",
            ),
            MODULE.Candidate(
                "patches/testing/0001-linux7.1-rc5-lru_marie-0.10.6.patch",
                "c" * 40,
                "https://example.invalid/lru-7.1.patch",
                0,
                (7, 1),
                "0.10.6",
            ),
        ]
        spec = {"name": "lru_marie", "repository": "firelzrd/lru_marie"}
        with mock.patch.object(MODULE, "upstream_candidates", return_value=candidates):
            selected = MODULE.resolve_github_component(spec, "6.18.45", None, ROOT)

        self.assertEqual(selected["selection"], "latest-native-series")
        self.assertEqual(
            selected["path"],
            "patches/testing/0001-linux6.18.22-lru_marie-0.10.6.patch",
        )

    def test_unversioned_port_requires_upstream_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.patch").write_bytes(PATCH)
            spec = self.base_spec()
            spec.pop("local_port_project_version")
            spec.pop("local_port_upstream_sha256")
            with mock.patch.object(
                MODULE,
                "upstream_candidates",
                return_value=[self.candidate(None)],
            ), mock.patch.object(MODULE, "request_bytes", return_value=PATCH):
                with self.assertRaisesRegex(MODULE.ResolveError, "must declare local_port_upstream_sha256"):
                    MODULE.resolve_github_component(spec, "6.18.45", None, root)


class MailboxLocalPortTests(unittest.TestCase):
    @staticmethod
    def spec(upstream_sha: str) -> dict[str, object]:
        return {
            "name": "mailbox_demo",
            "kind": "http_patch",
            "repository": "lore.kernel.org/linux-pm",
            "path": "demo@example.invalid",
            "commit": "demo@example.invalid",
            "target": "latest-mailbox-demo.patch",
            "urls": ["https://example.invalid/demo.mbox"],
            "mailbox": True,
            "local_port": "demo.port.patch",
            "port_for_kernel": "6.18.45",
            "local_port_upstream_sha256": upstream_sha,
        }

    def test_mailbox_is_decoded_before_hashing_and_upstream_is_selected_first(self) -> None:
        self.assertEqual(MODULE.decode_mailbox_patch(MBOX), DECODED_MBOX_PATCH)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.port.patch").write_bytes(PATCH)
            with mock.patch.object(MODULE, "request_bytes", return_value=MBOX):
                selected = MODULE.resolve_http_component(
                    self.spec(hashlib.sha256(DECODED_MBOX_PATCH).hexdigest()),
                    "6.18.45",
                    None,
                    root,
                )

        self.assertEqual(selected["origin"], "upstream-fixed")
        self.assertEqual(selected["selection"], "first-valid")
        self.assertEqual(selected["content_bytes"], DECODED_MBOX_PATCH)
        self.assertEqual(
            selected["fallback"],
            {
                "kind": "local-port",
                "path": "demo.port.patch",
                "kernel_version": "6.18.45",
                "upstream_sha256": hashlib.sha256(DECODED_MBOX_PATCH).hexdigest(),
            },
        )

    def test_changed_mailbox_payload_rejects_stale_local_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.port.patch").write_bytes(PATCH)
            with mock.patch.object(MODULE, "request_bytes", return_value=MBOX):
                with self.assertRaisesRegex(MODULE.ResolveError, "refresh and validate"):
                    MODULE.resolve_http_component(
                        self.spec("0" * 64), "6.18.45", None, root
                    )


class OfficialKernelSourceTests(unittest.TestCase):
    @staticmethod
    def config() -> dict[str, object]:
        return {
            "repository": "example/linux-integration",
            "series": "6.18",
            "tag_regex": r"^(?P<version>6\.18\.\d+)-valve(?P<valve>[0-9.]+)$",
            "official_source_index": "https://packages.example.invalid/sources/",
            "official_package_regex": (
                r"^linux-neptune-618-(?P<version>6\.18\.\d+)"
                r"\.valve(?P<valve>[0-9.]+)-(?P<pkgrel>\d+)\.src\.tar\.gz$"
            ),
        }

    def test_official_source_index_limits_the_selected_mirror_tag(self) -> None:
        listing = b'''<a href="linux-neptune-618-6.18.44.valve9-1.src.tar.gz">old</a>
<a href="linux-neptune-618-6.18.45.valve1-1.src.tar.gz">current</a>
<a href="linux-neptune-618-6.18.45.valve1-2.src.tar.gz">current rebuild</a>'''
        refs = [
            {
                "ref": "refs/tags/6.18.45-valve1",
                "object": {"sha": "a" * 40, "type": "commit"},
            },
            {
                "ref": "refs/tags/6.18.46-valve1",
                "object": {"sha": "b" * 40, "type": "commit"},
            },
        ]
        with (
            mock.patch.object(MODULE, "request_bytes", return_value=listing),
            mock.patch.object(MODULE, "request_json", return_value=refs),
        ):
            tag, commit, package = MODULE.resolve_kernel_tag(self.config(), None)

        self.assertEqual(tag, "6.18.45-valve1")
        self.assertEqual(commit, "a" * 40)
        self.assertEqual(package["filename"], "linux-neptune-618-6.18.45.valve1-2.src.tar.gz")
        self.assertEqual(package["pkgrel"], 2)

    def test_missing_official_mirror_tag_is_rejected(self) -> None:
        listing = b'<a href="linux-neptune-618-6.18.45.valve1-1.src.tar.gz">current</a>'
        refs = [
            {
                "ref": "refs/tags/6.18.44-valve9",
                "object": {"sha": "a" * 40, "type": "commit"},
            }
        ]
        with (
            mock.patch.object(MODULE, "request_bytes", return_value=listing),
            mock.patch.object(MODULE, "request_json", return_value=refs),
        ):
            with self.assertRaisesRegex(MODULE.ResolveError, "requires mirror tag"):
                MODULE.resolve_kernel_tag(self.config(), None)



class NapLatestUpstreamTests(unittest.TestCase):
    def test_testing_065_outweighs_older_native_051_on_both_kernel_series(self) -> None:
        for kernel, compatibility in (("6.18.53", 2), ("7.2", 0)):
            with self.subTest(kernel=kernel):
                spec = {
                    "name": "nap",
                    "repository": "firelzrd/nap",
                    "port_for_kernel": ".".join(kernel.split(".")[:2]),
                    "port_when_incompatible": True,
                    "adaptive_port": "nap-direct-apply-" + ".".join(kernel.split(".")[:2]),
                }
                native_old = MODULE.Candidate(
                    "patches/stable/0001-6.18.3-nap-v0.5.1.patch",
                    "a" * 40,
                    "https://example.invalid/nap-old.patch",
                    compatibility,
                    (6, 18, 3),
                    "0.5.1",
                )
                testing_new = MODULE.Candidate(
                    "patches/testing/0001-6.12-nap-v0.6.5.patch",
                    "b" * 40,
                    "https://example.invalid/nap-new.patch",
                    0,
                    (6, 12),
                    "0.6.5",
                )
                with (
                    mock.patch.object(
                        MODULE, "upstream_candidates", return_value=[native_old, testing_new]
                    ),
                    mock.patch.object(MODULE, "request_bytes", return_value=PATCH),
                ):
                    record = MODULE.resolve_github_component(spec, kernel, None, ROOT)
                self.assertEqual(record["path"], testing_new.path)
                self.assertEqual(record["project_version"], "0.6.5")
                self.assertEqual(record["origin"], "adaptive-port")
                self.assertEqual(record["selection"], "latest-release-adaptive-port")
                self.assertEqual(record["adapter"], spec["adaptive_port"])
                self.assertEqual(record["content_bytes"], PATCH)



class SameReleaseKernelPriorityTests(unittest.TestCase):
    def test_stale_reviewed_revision_is_never_used_as_native_fallback(self) -> None:
        spec = {
            "name": "adios",
            "local_port": "6.18-adios-3.3.0r2.port.patch",
            "local_port_project_version": "3.3.0r2",
            "local_port_upstream_sha256": "a" * 64,
        }
        self.assertIsNone(
            MODULE.fallback_metadata(spec, "6.18.53", "3.3.0")
        )
        fallback = MODULE.fallback_metadata(spec, "6.18.53", "3.3.0r2")
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback["project_version"], "3.3.0r2")
        self.assertEqual(fallback["kernel_version"], "6.18.53")

    def test_version_11_prefers_matching_kernel_618_or_72_not_73(self) -> None:
        for kernel, native_suffix, native_version in (
            ("6.18.53", "6.18.22", (6, 18, 22)),
            ("7.2", "7.2-rc1", (7, 2)),
        ):
            with self.subTest(kernel=kernel):
                native = MODULE.Candidate(
                    f"patches/testing/0001-linux{native_suffix}-demo-1.1.patch",
                    "a" * 40, "https://example.invalid/native.patch",
                    2, native_version, "1.1",
                )
                foreign = MODULE.Candidate(
                    "patches/testing/0001-linux7.3-rc1-demo-1.1.patch",
                    "b" * 40, "https://example.invalid/foreign.patch",
                    0, (7, 3), "1.1",
                )
                with mock.patch.object(
                    MODULE, "upstream_candidates", return_value=[foreign, native],
                ):
                    selected = MODULE.resolve_github_component(
                        {"name": "demo", "repository": "example/demo"},
                        kernel, None, ROOT,
                    )
                self.assertEqual(selected["path"], native.path)
                self.assertEqual(selected["origin"], "upstream-native")
                self.assertEqual(selected["selection"], "latest-native-series")
                self.assertEqual(selected["latest_upstream_project_version"], "1.1")

    def test_revision_r2_of_same_base_prefers_618_specific_upstream_patch(self) -> None:
        native = MODULE.Candidate(
            "patches/testing/0001-linux6.18.22-lru_marie-0.12.0.patch",
            "a" * 40, "https://example.invalid/marie-native.patch",
            2, (6, 18, 22), "0.12.0",
        )
        foreign_revision = MODULE.Candidate(
            "patches/testing/0001-linux7.3-rc1-lru_marie-0.12.0r2.patch",
            "b" * 40, "https://example.invalid/marie-r2.patch",
            0, (7, 3), "0.12.0r2",
        )
        with mock.patch.object(
            MODULE, "upstream_candidates", return_value=[foreign_revision, native],
        ):
            selected = MODULE.resolve_github_component(
                {"name": "lru_marie", "repository": "firelzrd/lru_marie"},
                "6.18.53", None, ROOT,
            )
        self.assertEqual(selected["path"], native.path)
        self.assertEqual(selected["project_version"], "0.12.0")
        self.assertEqual(selected["latest_upstream_project_version"], "0.12.0r2")
        self.assertEqual(selected["selection"], "latest-native-series")

    def test_newer_release_without_native_uses_reviewed_port_not_old_native(self) -> None:
        old_native = MODULE.Candidate(
            "patches/stable/0001-6.18.3-nap-v0.5.1.patch",
            "a" * 40, "https://example.invalid/old.patch",
            2, (6, 18, 3), "0.5.1",
        )
        newer_far = MODULE.Candidate(
            "patches/testing/0001-6.12-nap-v0.6.5.patch",
            "b" * 40, "https://example.invalid/far.patch",
            0, (6, 12), "0.6.5",
        )
        newer_near = MODULE.Candidate(
            "patches/testing/0001-6.16-nap-v0.6.5.patch",
            "c" * 40, "https://example.invalid/near.patch",
            0, (6, 16), "0.6.5",
        )
        spec = {
            "name": "nap",
            "repository": "firelzrd/nap",
            "adaptive_port": "nap-direct-apply-6.18",
            "port_when_incompatible": True,
        }
        with (
            mock.patch.object(
                MODULE, "upstream_candidates",
                return_value=[old_native, newer_far, newer_near],
            ),
            mock.patch.object(MODULE, "request_bytes", return_value=PATCH),
        ):
            selected = MODULE.resolve_github_component(spec, "6.18.53", None, ROOT)
        self.assertEqual(selected["path"], newer_near.path)
        self.assertEqual(selected["project_version"], "0.6.5")
        self.assertEqual(selected["latest_upstream_project_version"], "0.6.5")
        self.assertEqual(selected["origin"], "adaptive-port")
        self.assertEqual(selected["selection"], "latest-release-adaptive-port")

    def test_newer_native_version_wins_over_older_native_version(self) -> None:
        older = MODULE.Candidate(
            "patches/stable/0001-linux6.18.3-demo-1.0.patch",
            "a" * 40, "https://example.invalid/old.patch",
            3, (6, 18, 3), "1.0",
        )
        latest = MODULE.Candidate(
            "patches/testing/0001-linux6.18.22-demo-1.1.patch",
            "b" * 40, "https://example.invalid/new.patch",
            2, (6, 18, 22), "1.1",
        )
        with mock.patch.object(
            MODULE, "upstream_candidates", return_value=[older, latest],
        ):
            selected = MODULE.resolve_github_component(
                {"name": "demo", "repository": "example/demo"},
                "6.18.3", None, ROOT,
            )
        self.assertEqual(selected["path"], latest.path)
        self.assertEqual(selected["project_version"], "1.1")

    def test_missing_native_version_and_port_policy_fails_closed(self) -> None:
        foreign = MODULE.Candidate(
            "patches/testing/0001-linux7.3-demo-1.1.patch",
            "a" * 40, "https://example.invalid/foreign.patch",
            0, (7, 3), "1.1",
        )
        with mock.patch.object(MODULE, "upstream_candidates", return_value=[foreign]):
            with self.assertRaisesRegex(MODULE.ResolveError, "tracked port is required"):
                MODULE.resolve_github_component(
                    {"name": "demo", "repository": "example/demo"},
                    "6.18.53", None, ROOT,
                )


if __name__ == "__main__":
    unittest.main()
