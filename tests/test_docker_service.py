from unittest.mock import MagicMock
from aesiron.services.docker import find_next_available_port, is_port_in_use


def test_is_port_in_use_returns_false_when_free(mocker):
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 111 # EHOSTUNREACH or similar
    
    assert is_port_in_use(8501) is False

def test_is_port_in_use_returns_true_when_taken(mocker):
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0 # Success means port is taken
    
    assert is_port_in_use(8501) is True

def test_find_next_available_port_checks_running_containers(mocker, tmp_path):
    # Mock containers
    fake_container = MagicMock()
    fake_container.attrs = {
        "NetworkSettings": {
            "Ports": {
                "8501/tcp": [{"HostPort": "8501"}]
            }
        }
    }
    mocker.patch("aesiron.services.docker.get_running_containers", return_value=[fake_container])
    
    # Mock no compose files in armory
    mocker.patch("pathlib.Path.glob", return_value=[])
    
    # Mock socket to always return free except for containers
    mocker.patch("aesiron.services.docker.is_port_in_use", side_effect=lambda p: p == 8501)
    
    port = find_next_available_port(start_port=8501, armory_path=str(tmp_path))
    assert port == 8502

def test_find_next_available_port_checks_compose_files(mocker, tmp_path):
    mocker.patch("aesiron.services.docker.get_running_containers", return_value=[])
    mocker.patch("aesiron.services.docker.is_port_in_use", return_value=False)
    
    # Create a fake app with a compose.yml using port 8505
    app_dir = tmp_path / "app1"
    app_dir.mkdir()
    compose_file = app_dir / "compose.yml"
    compose_file.write_text("""
services:
  app1:
    ports:
      - "8505:8501"
""", encoding="utf-8")
    
    # find_next_available_port uses Path(armory_path).glob("**/compose.yml")
    # We need to make sure the mock returns our file
    mocker.patch("pathlib.Path.glob", return_value=[compose_file])
    
    port = find_next_available_port(start_port=8501, armory_path=str(tmp_path))
    assert port == 8501 # Should be 8501 because 8501 is free and 8505 is the one taken
    
    # If we start at 8505, it should skip to 8506
    port = find_next_available_port(start_port=8505, armory_path=str(tmp_path))
    assert port == 8506
