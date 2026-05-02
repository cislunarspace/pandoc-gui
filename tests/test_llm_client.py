# tests/test_llm_client.py
import pytest
import urllib.error
from unittest.mock import patch, MagicMock


class TestLLMClient:
    """Tests for the llm_client module."""

    def test_call_llm_success(self):
        from pandoc_gui.llm_client import call_llm
        import json

        mock_response_body = json.dumps({"choices": [{"message": {"content": "旧||新"}}]}).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_response_body

        with patch("pandoc_gui.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
            mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

            result = call_llm("http://example.com/v1/chat/completions", "test-key", "gpt-4", ["旧"])

        assert result == "旧||新"
        mock_urlopen.assert_called_once()

    def test_call_llm_http_error(self):
        from pandoc_gui.llm_client import call_llm

        with patch("pandoc_gui.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="http://example.com",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=None,
            )

            with pytest.raises(RuntimeError) as exc_info:
                call_llm("http://example.com/v1/chat/completions", "bad-key", "gpt-4", ["标题"])

            assert "401" in str(exc_info.value)

    def test_call_llm_url_error(self):
        from pandoc_gui.llm_client import call_llm

        with patch("pandoc_gui.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(RuntimeError) as exc_info:
                call_llm("http://bad-host/v1/chat/completions", "test-key", "gpt-4", ["标题"])

            assert "failed" in str(exc_info.value)

    def test_call_llm_sends_correct_payload(self):
        from pandoc_gui.llm_client import call_llm
        import json

        captured_request = {}

        def capture_urlopen(req, timeout=None):
            captured_request["url"] = req.full_url
            captured_request["headers"] = dict(req.headers)
            captured_request["data"] = json.loads(req.data.decode("utf-8"))
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "choices": [{"message": {"content": ""}}]
            }).encode("utf-8")
            # Return a context manager
            mock_cm = MagicMock()
            mock_cm.__enter__ = MagicMock(return_value=mock_resp)
            mock_cm.__exit__ = MagicMock(return_value=False)
            return mock_cm

        with patch("pandoc_gui.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = capture_urlopen
            call_llm(
                "http://example.com/v1/chat/completions",
                "my-secret-key",
                "gpt-4",
                ["标题一", "标题二"],
            )

        assert captured_request["url"] == "http://example.com/v1/chat/completions"
        # Check data was sent (payload format verified by structure)
        payload = captured_request["data"]
        assert payload["model"] == "gpt-4"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert "标题优化" in payload["messages"][0]["content"]
        assert "标题一" in payload["messages"][1]["content"]
