from __future__ import absolute_import
from __future__ import unicode_literals

import logging

import docker
import pytest

from compose import container
from compose.cli.errors import UserError
from compose.cli.formatter import ConsoleWarningFormatter
from compose.cli.main import call_docker
from compose.cli.main import convergence_strategy_from_opts
from compose.cli.main import filter_containers_to_service_names
from compose.cli.main import setup_console_handler
from compose.cli.main import warn_for_swarm_mode
from compose.service import ConvergenceStrategy
from tests import mock


def mock_container(service, number):
    return mock.create_autospec(
        container.Container,
        service=service,
        number=number,
        name_without_project='{0}_{1}'.format(service, number))


@pytest.fixture
def logging_handler():
    stream = mock.Mock()
    stream.isatty.return_value = True
    return logging.StreamHandler(stream=stream)


class TestCLIMainTestCase(object):

    def test_filter_containers_to_service_names(self):
        containers = [
            mock_container('web', 1),
            mock_container('web', 2),
            mock_container('db', 1),
            mock_container('other', 1),
            mock_container('another', 1),
        ]
        service_names = ['web', 'db']
        actual = filter_containers_to_service_names(containers, service_names)
        assert actual == containers[:3]

    def test_filter_containers_to_service_names_all(self):
        containers = [
            mock_container('web', 1),
            mock_container('db', 1),
            mock_container('other', 1),
        ]
        service_names = []
        actual = filter_containers_to_service_names(containers, service_names)
        assert actual == containers

    def test_warning_in_swarm_mode(self):
        mock_client = mock.create_autospec(docker.APIClient)
        mock_client.info.return_value = {'Swarm': {'LocalNodeState': 'active'}}

        with mock.patch('compose.cli.main.log') as fake_log:
            warn_for_swarm_mode(mock_client)
            assert fake_log.warn.call_count == 1


class TestSetupConsoleHandlerTestCase(object):

    def test_with_tty_verbose(self, logging_handler):
        setup_console_handler(logging_handler, True)
        assert type(logging_handler.formatter) == ConsoleWarningFormatter
        assert '%(name)s' in logging_handler.formatter._fmt
        assert '%(funcName)s' in logging_handler.formatter._fmt

    def test_with_tty_not_verbose(self, logging_handler):
        setup_console_handler(logging_handler, False)
        assert type(logging_handler.formatter) == ConsoleWarningFormatter
        assert '%(name)s' not in logging_handler.formatter._fmt
        assert '%(funcName)s' not in logging_handler.formatter._fmt

    def test_with_not_a_tty(self, logging_handler):
        logging_handler.stream.isatty.return_value = False
        setup_console_handler(logging_handler, False)
        assert type(logging_handler.formatter) == logging.Formatter


class TestConvergeStrategyFromOptsTestCase(object):

    def test_invalid_opts(self):
        options = {'--force-recreate': True, '--no-recreate': True}
        with pytest.raises(UserError):
            convergence_strategy_from_opts(options)

    def test_always(self):
        options = {'--force-recreate': True, '--no-recreate': False}
        assert (
            convergence_strategy_from_opts(options) ==
            ConvergenceStrategy.always
        )

    def test_never(self):
        options = {'--force-recreate': False, '--no-recreate': True}
        assert (
            convergence_strategy_from_opts(options) ==
            ConvergenceStrategy.never
        )

    def test_changed(self):
        options = {'--force-recreate': False, '--no-recreate': False}
        assert (
            convergence_strategy_from_opts(options) ==
            ConvergenceStrategy.changed
        )


def mock_find_executable(exe):
    return exe


@mock.patch('compose.cli.main.find_executable', mock_find_executable)
class TestCallDocker(object):
    def test_simple_no_options(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {})

        assert fake_call.call_args[0][0] == ['docker', 'ps']

    def test_simple_tls_option(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {'--tls': True})

        assert fake_call.call_args[0][0] == ['docker', '--tls', 'ps']

    def test_advanced_tls_options(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {
                '--tls': True,
                '--tlscacert': './ca.pem',
                '--tlscert': './cert.pem',
                '--tlskey': './key.pem',
            })

        assert fake_call.call_args[0][0] == [
            'docker', '--tls', '--tlscacert', './ca.pem', '--tlscert',
            './cert.pem', '--tlskey', './key.pem', 'ps'
        ]

    def test_with_host_option(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {'--host': 'tcp://mydocker.net:2333'})

        assert fake_call.call_args[0][0] == [
            'docker', '--host', 'tcp://mydocker.net:2333', 'ps'
        ]

    def test_with_http_host(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {'--host': 'http://mydocker.net:2333'})

        assert fake_call.call_args[0][0] == [
            'docker', '--host', 'tcp://mydocker.net:2333', 'ps',
        ]

    def test_with_host_option_shorthand_equal(self):
        with mock.patch('subprocess.call') as fake_call:
            call_docker(['ps'], {'--host': '=tcp://mydocker.net:2333'})

        assert fake_call.call_args[0][0] == [
            'docker', '--host', 'tcp://mydocker.net:2333', 'ps'
        ]
