import json
from unittest.mock import patch

import httpx
from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()

def test_login(tmp_path):
    with patch("src.cli.main.CONFIG_FILE", tmp_path / "config.json"):
        with patch("src.cli.main.CONFIG_DIR", tmp_path):
            result = runner.invoke(app, ["login", "--user", "u1", "--tenant", "t1"])
            assert result.exit_code == 0
            assert "Successfully logged in as user 'u1' for tenant 't1'" in result.stdout
            
            with open(tmp_path / "config.json") as f:
                config = json.load(f)
                assert config["user_id"] == "u1"
                assert config["tenant_id"] == "t1"

def test_whoami(tmp_path):
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump({"user_id": "u2", "tenant_id": "t2"}, f)
        
    with patch("src.cli.main.CONFIG_FILE", config_file):
        with patch("src.cli.main.CONFIG_DIR", tmp_path):
            result = runner.invoke(app, ["whoami"])
            assert result.exit_code == 0
            assert "u2" in result.stdout
            assert "t2" in result.stdout

def test_ask_success(tmp_path):
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump({"user_id": "u1", "tenant_id": "t1"}, f)
        
    mock_response = httpx.Response(
        200, 
        json={
            "status": "grounded",
            "text": "This is the answer.",
            "citations": [{"claim": "fact", "chunk_ids": ["c1"]}],
            "route": "direct-retrieve",
            "trace_id": "123"
        }
    )
        
    with patch("src.cli.main.CONFIG_FILE", config_file):
        with patch("src.cli.main.CONFIG_DIR", tmp_path):
            with patch("httpx.post", return_value=mock_response) as mock_post:
                result = runner.invoke(app, ["ask", "What is it?"])
                assert result.exit_code == 0
                assert "This is the answer." in result.stdout
                assert "Sources" in result.stdout
                assert "c1" in result.stdout
                
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert kwargs["headers"]["X-User-Id"] == "u1"
                assert kwargs["headers"]["X-Tenant-Id"] == "t1"
                assert kwargs["json"]["query"] == "What is it?"

def test_ask_denied(tmp_path):
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump({"user_id": "u1", "tenant_id": "t1"}, f)
        
    mock_response = httpx.Response(403, json={"detail": "Tenant mismatch"})
        
    with patch("src.cli.main.CONFIG_FILE", config_file):
        with patch("src.cli.main.CONFIG_DIR", tmp_path):
            with patch("httpx.post", return_value=mock_response):
                result = runner.invoke(app, ["ask", "What is it?"])
                assert result.exit_code == 1
                assert "Access denied: Tenant mismatch (403)" in result.stdout

def test_ask_not_logged_in(tmp_path):
    with patch("src.cli.main.CONFIG_FILE", tmp_path / "config.json"):
        with patch("src.cli.main.CONFIG_DIR", tmp_path):
            result = runner.invoke(app, ["ask", "What is it?"])
            assert result.exit_code == 1
            assert "Not logged in" in result.stdout
