from pathlib import Path
from unittest.mock import MagicMock


class TestInfraHelpers:
    def test_get_app_hostname_uses_iron_zone(self):
        from aesiron.services.infra import get_app_hostname

        assert get_app_hostname("Financeiro App") == "financeiro-app.iron"

    def test_build_dnsmasq_config_uses_wildcard_zone_and_upstreams(self):
        from aesiron.services.infra import build_dnsmasq_config

        config = build_dnsmasq_config("192.168.0.10", ["9.9.9.9", "1.1.1.1"])

        assert "address=/.iron/192.168.0.10" in config
        assert "server=9.9.9.9" in config
        assert "server=1.1.1.1" in config

    def test_build_gateway_config_routes_hostname_to_container(self):
        from aesiron.services.infra import build_gateway_config

        fake_container = MagicMock()
        fake_container.name = "app-aesiron-demo-app"
        fake_container.attrs = {
            "NetworkSettings": {"Ports": {"8600/tcp": [{"HostPort": "8600"}]}}
        }

        config = build_gateway_config([fake_container])

        assert "server_name demo-app.iron;" in config
        assert "proxy_pass http://app-aesiron-demo-app:8600;" in config
        assert "proxy_set_header Upgrade $http_upgrade;" in config
        assert "proxy_buffering off;" in config

    def test_extract_container_target_port_prefers_bound_port(self):
        from aesiron.services.infra import extract_container_target_port

        fake_container = MagicMock()
        fake_container.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "8501/tcp": None,
                    "8502/tcp": [{"HostPort": "8502"}],
                }
            },
            "Config": {"ExposedPorts": {"8501/tcp": {}, "8502/tcp": {}}},
        }

        assert extract_container_target_port(fake_container) == "8502"

    def test_get_upstream_nameservers_filters_loopback(self, tmp_path):
        from aesiron.services.infra import get_upstream_nameservers

        resolv_conf = tmp_path / "resolv.conf"
        resolv_conf.write_text(
            "nameserver 127.0.0.53\nnameserver 192.168.0.1\n",
            encoding="utf-8",
        )

        assert get_upstream_nameservers(resolv_conf) == ["192.168.0.1"]

    def test_get_dns_setup_lines_includes_manual_dns_guidance(self, mocker, tmp_path):
        from aesiron.services.infra import get_dns_setup_lines

        mocker.patch("aesiron.services.infra.get_infra_dir", return_value=Path(tmp_path / ".aesiron-infra"))
        mocker.patch("aesiron.services.docker.get_host_ip", return_value="192.168.0.10")

        lines = get_dns_setup_lines("/tmp/armory")

        assert any("192.168.0.10" in line for line in lines)
        assert any(".iron" in line for line in lines)

    def test_resolve_docker_bind_path_maps_armory_volume_when_host_pwd_exists(self):
        from aesiron.services.infra import resolve_docker_bind_path

        resolved = resolve_docker_bind_path(
            Path("/armory/.aesiron-infra/nginx.conf"),
            env={"HOST_PWD": "/home/user/projects/aesiron"},
        )

        assert resolved == Path("/home/user/projects/aesiron/.aesiron-infra/nginx.conf")

    def test_render_hosts_file_replaces_only_aesiron_block(self):
        from aesiron.services.infra import HOSTS_BEGIN_MARKER, HOSTS_END_MARKER, render_hosts_file

        current = "127.0.0.1 localhost\n\n# >>> aesiron dns >>>\n1.1.1.1 old.iron\n# <<< aesiron dns <<<\n"
        block = "\n".join([HOSTS_BEGIN_MARKER, "192.168.0.10 demo.iron", HOSTS_END_MARKER])

        rendered = render_hosts_file(current, block)

        assert "127.0.0.1 localhost" in rendered
        assert "192.168.0.10 demo.iron" in rendered
        assert "old.iron" not in rendered

    def test_sync_network_infra_recreates_dns_and_gateway(self, mocker):
        from aesiron.services.infra import sync_network_infra

        fake_container = MagicMock()
        mocker.patch("aesiron.services.docker.get_host_ip", return_value="192.168.0.10")
        mocker.patch("aesiron.services.docker.get_running_containers", return_value=[fake_container])
        mock_gateway = mocker.patch("aesiron.services.infra.ensure_gateway_service", return_value="gateway")
        mock_dns = mocker.patch("aesiron.services.infra.ensure_dns_service", return_value="dns")

        result = sync_network_infra("/tmp/armory")

        mock_gateway.assert_called_once_with([fake_container], "/tmp/armory")
        mock_dns.assert_called_once_with("192.168.0.10", "/tmp/armory")
        assert result == {"gateway": "gateway", "dns": "dns", "host_ip": "192.168.0.10"}

    def test_sync_network_infra_cleans_state_when_no_apps_are_running(self, mocker):
        from aesiron.services.infra import sync_network_infra

        mocker.patch("aesiron.services.docker.get_running_containers", return_value=[])
        mock_remove_containers = mocker.patch("aesiron.services.infra.remove_infra_containers")
        mock_remove_state = mocker.patch("aesiron.services.infra.remove_infra_state")

        result = sync_network_infra("/tmp/armory")

        mock_remove_containers.assert_called_once_with()
        mock_remove_state.assert_called_once_with("/tmp/armory")
        assert result == {"gateway": None, "dns": None, "host_ip": None}

    def test_configure_local_dns_client_updates_hosts_file(self, mocker):
        from aesiron.services.infra import configure_local_dns_client

        mocker.patch("aesiron.services.docker.get_host_ip", return_value="192.168.0.10")
        mocker.patch("aesiron.services.docker.get_running_app_names", return_value=["demo"])
        mocker.patch("aesiron.services.infra.read_system_hosts", return_value="127.0.0.1 localhost\n")
        mock_write_hosts = mocker.patch("aesiron.services.infra.write_system_hosts")
        mock_write_state = mocker.patch("aesiron.services.infra.write_local_dns_state")

        lines = configure_local_dns_client("/tmp/armory")

        mock_write_hosts.assert_called_once()
        mock_write_state.assert_called_once_with(["demo.iron"], "/tmp/armory")
        written = mock_write_hosts.call_args.args[0]
        assert "demo.iron" in written
        assert any("192.168.0.10" in line for line in lines)

    def test_reset_local_dns_client_removes_only_aesiron_block(self, mocker):
        from aesiron.services.infra import reset_local_dns_client

        mocker.patch(
            "aesiron.services.infra.read_system_hosts",
            return_value="127.0.0.1 localhost\n\n# >>> aesiron dns >>>\n192.168.0.10 demo.iron\n# <<< aesiron dns <<<\n",
        )
        mock_write_hosts = mocker.patch("aesiron.services.infra.write_system_hosts")
        mock_remove_state = mocker.patch("aesiron.services.infra.remove_local_dns_state")

        lines = reset_local_dns_client("/tmp/armory")

        written = mock_write_hosts.call_args.args[0]
        mock_remove_state.assert_called_once_with("/tmp/armory")
        assert "demo.iron" not in written
        assert "127.0.0.1 localhost" in written
        assert any("removidas" in line.lower() for line in lines)

    def test_read_system_hosts_uses_helper_inside_container(self, mocker):
        from aesiron.services.infra import read_system_hosts

        mocker.patch("aesiron.services.infra.is_containerized_runtime", return_value=True)
        mocker.patch("aesiron.services.infra.read_host_file_via_helper", return_value="127.0.0.1 localhost\n")

        assert read_system_hosts() == "127.0.0.1 localhost\n"

    def test_read_local_dns_state_returns_saved_hostnames(self, tmp_path):
        from aesiron.services.infra import read_local_dns_state, write_local_dns_state

        write_local_dns_state(["demo.iron", "api.iron"], str(tmp_path))

        assert read_local_dns_state(str(tmp_path)) == ["api.iron", "demo.iron"]
