# encoding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

import docker
import pytest
from docker.errors import NotFound

from .. import mock
from .. import unittest
from compose.config.config import Config
from compose.config.types import VolumeFromSpec
from compose.const import COMPOSEFILE_V1 as V1
from compose.const import COMPOSEFILE_V2_0 as V2_0
from compose.const import COMPOSEFILE_V2_4 as V2_4
from compose.const import LABEL_SERVICE
from compose.container import Container
from compose.errors import OperationFailedError
from compose.project import NoSuchService
from compose.project import Project
from compose.project import ProjectError
from compose.service import ImageType
from compose.service import Service


class ProjectTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.create_autospec(docker.APIClient)
        self.mock_client._general_configs = {}
        self.mock_client.api_version = docker.constants.DEFAULT_DOCKER_API_VERSION

    def test_from_config_v1(self):
        config = Config(
            version=V1,
            services=[
                {
                    'name': 'web',
                    'image': 'busybox:latest',
                },
                {
                    'name': 'db',
                    'image': 'busybox:latest',
                },
            ],
            networks=None,
            volumes=None,
            secrets=None,
            configs=None,
        )
        project = Project.from_config(
            name='composetest',
            config_data=config,
            client=None,
        )
        assert len(project.services) == 2
        assert project.get_service('web').name == 'web'
        assert project.get_service('web').options['image'] == 'busybox:latest'
        assert project.get_service('db').name == 'db'
        assert project.get_service('db').options['image'] == 'busybox:latest'
        assert not project.networks.use_networking

    @mock.patch('compose.network.Network.true_name', lambda n: n.full_name)
    def test_from_config_v2(self):
        config = Config(
            version=V2_0,
            services=[
                {
                    'name': 'web',
                    'image': 'busybox:latest',
                },
                {
                    'name': 'db',
                    'image': 'busybox:latest',
                },
            ],
            networks=None,
            volumes=None,
            secrets=None,
            configs=None,
        )
        project = Project.from_config('composetest', config, None)
        assert len(project.services) == 2
        assert project.networks.use_networking

    def test_get_service(self):
        web = Service(
            project='composetest',
            name='web',
            client=None,
            image="busybox:latest",
        )
        project = Project('test', [web], None)
        assert project.get_service('web') == web

    def test_get_services_returns_all_services_without_args(self):
        web = Service(
            project='composetest',
            name='web',
            image='foo',
        )
        console = Service(
            project='composetest',
            name='console',
            image='foo',
        )
        project = Project('test', [web, console], None)
        assert project.get_services() == [web, console]

    def test_get_services_returns_listed_services_with_args(self):
        web = Service(
            project='composetest',
            name='web',
            image='foo',
        )
        console = Service(
            project='composetest',
            name='console',
            image='foo',
        )
        project = Project('test', [web, console], None)
        assert project.get_services(['console']) == [console]

    def test_get_services_with_include_links(self):
        db = Service(
            project='composetest',
            name='db',
            image='foo',
        )
        web = Service(
            project='composetest',
            name='web',
            image='foo',
            links=[(db, 'database')]
        )
        cache = Service(
            project='composetest',
            name='cache',
            image='foo'
        )
        console = Service(
            project='composetest',
            name='console',
            image='foo',
            links=[(web, 'web')]
        )
        project = Project('test', [web, db, cache, console], None)
        assert project.get_services(['console'], include_deps=True) == [db, web, console]

    def test_get_services_removes_duplicates_following_links(self):
        db = Service(
            project='composetest',
            name='db',
            image='foo',
        )
        web = Service(
            project='composetest',
            name='web',
            image='foo',
            links=[(db, 'database')]
        )
        project = Project('test', [web, db], None)
        assert project.get_services(['web', 'db'], include_deps=True) == [db, web]

    def test_use_volumes_from_container(self):
        container_id = 'aabbccddee'
        container_dict = dict(Name='aaa', Id=container_id)
        self.mock_client.inspect_container.return_value = container_dict
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[{
                    'name': 'test',
                    'image': 'busybox:latest',
                    'volumes_from': [VolumeFromSpec('aaa', 'rw', 'container')]
                }],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        assert project.get_service('test')._get_volumes_from() == [container_id + ":rw"]

    def test_use_volumes_from_service_no_container(self):
        container_name = 'test_vol_1'
        self.mock_client.containers.return_value = [
            {
                "Name": container_name,
                "Names": [container_name],
                "Id": container_name,
                "Image": 'busybox:latest'
            }
        ]
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'vol',
                        'image': 'busybox:latest'
                    },
                    {
                        'name': 'test',
                        'image': 'busybox:latest',
                        'volumes_from': [VolumeFromSpec('vol', 'rw', 'service')]
                    }
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        assert project.get_service('test')._get_volumes_from() == [container_name + ":rw"]

    @mock.patch('compose.network.Network.true_name', lambda n: n.full_name)
    def test_use_volumes_from_service_container(self):
        container_ids = ['aabbccddee', '12345']

        project = Project.from_config(
            name='test',
            client=None,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'vol',
                        'image': 'busybox:latest'
                    },
                    {
                        'name': 'test',
                        'image': 'busybox:latest',
                        'volumes_from': [VolumeFromSpec('vol', 'rw', 'service')]
                    }
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        with mock.patch.object(Service, 'containers') as mock_return:
            mock_return.return_value = [
                mock.Mock(id=container_id, spec=Container)
                for container_id in container_ids]
            assert (
                project.get_service('test')._get_volumes_from() ==
                [container_ids[0] + ':rw']
            )

    def test_events_legacy(self):
        services = [Service(name='web'), Service(name='db')]
        project = Project('test', services, self.mock_client)
        self.mock_client.api_version = '1.21'
        self.mock_client.events.return_value = iter([
            {
                'status': 'create',
                'from': 'example/image',
                'id': 'abcde',
                'time': 1420092061,
                'timeNano': 14200920610000002000,
            },
            {
                'status': 'attach',
                'from': 'example/image',
                'id': 'abcde',
                'time': 1420092061,
                'timeNano': 14200920610000003000,
            },
            {
                'status': 'create',
                'from': 'example/other',
                'id': 'bdbdbd',
                'time': 1420092061,
                'timeNano': 14200920610000005000,
            },
            {
                'status': 'create',
                'from': 'example/db',
                'id': 'ababa',
                'time': 1420092061,
                'timeNano': 14200920610000004000,
            },
            {
                'status': 'destroy',
                'from': 'example/db',
                'id': 'eeeee',
                'time': 1420092061,
                'timeNano': 14200920610000004000,
            },
        ])

        def dt_with_microseconds(dt, us):
            return datetime.datetime.fromtimestamp(dt).replace(microsecond=us)

        def get_container(cid):
            if cid == 'eeeee':
                raise NotFound(None, None, "oops")
            if cid == 'abcde':
                name = 'web'
                labels = {LABEL_SERVICE: name}
            elif cid == 'ababa':
                name = 'db'
                labels = {LABEL_SERVICE: name}
            else:
                labels = {}
                name = ''
            return {
                'Id': cid,
                'Config': {'Labels': labels},
                'Name': '/project_%s_1' % name,
            }

        self.mock_client.inspect_container.side_effect = get_container

        events = project.events()

        events_list = list(events)
        # Assert the return value is a generator
        assert not list(events)
        assert events_list == [
            {
                'type': 'container',
                'service': 'web',
                'action': 'create',
                'id': 'abcde',
                'attributes': {
                    'name': 'project_web_1',
                    'image': 'example/image',
                },
                'time': dt_with_microseconds(1420092061, 2),
                'container': Container(None, {'Id': 'abcde'}),
            },
            {
                'type': 'container',
                'service': 'web',
                'action': 'attach',
                'id': 'abcde',
                'attributes': {
                    'name': 'project_web_1',
                    'image': 'example/image',
                },
                'time': dt_with_microseconds(1420092061, 3),
                'container': Container(None, {'Id': 'abcde'}),
            },
            {
                'type': 'container',
                'service': 'db',
                'action': 'create',
                'id': 'ababa',
                'attributes': {
                    'name': 'project_db_1',
                    'image': 'example/db',
                },
                'time': dt_with_microseconds(1420092061, 4),
                'container': Container(None, {'Id': 'ababa'}),
            },
        ]

    def test_events(self):
        services = [Service(name='web'), Service(name='db')]
        project = Project('test', services, self.mock_client)
        self.mock_client.api_version = '1.35'
        self.mock_client.events.return_value = iter([
            {
                'status': 'create',
                'from': 'example/image',
                'Type': 'container',
                'Actor': {
                    'ID': 'abcde',
                    'Attributes': {
                        'com.docker.compose.project': 'test',
                        'com.docker.compose.service': 'web',
                        'image': 'example/image',
                        'name': 'test_web_1',
                    }
                },
                'id': 'abcde',
                'time': 1420092061,
                'timeNano': 14200920610000002000,
            },
            {
                'status': 'attach',
                'from': 'example/image',
                'Type': 'container',
                'Actor': {
                    'ID': 'abcde',
                    'Attributes': {
                        'com.docker.compose.project': 'test',
                        'com.docker.compose.service': 'web',
                        'image': 'example/image',
                        'name': 'test_web_1',
                    }
                },
                'id': 'abcde',
                'time': 1420092061,
                'timeNano': 14200920610000003000,
            },
            {
                'status': 'create',
                'from': 'example/other',
                'Type': 'container',
                'Actor': {
                    'ID': 'bdbdbd',
                    'Attributes': {
                        'image': 'example/other',
                        'name': 'shrewd_einstein',
                    }
                },
                'id': 'bdbdbd',
                'time': 1420092061,
                'timeNano': 14200920610000005000,
            },
            {
                'status': 'create',
                'from': 'example/db',
                'Type': 'container',
                'Actor': {
                    'ID': 'ababa',
                    'Attributes': {
                        'com.docker.compose.project': 'test',
                        'com.docker.compose.service': 'db',
                        'image': 'example/db',
                        'name': 'test_db_1',
                    }
                },
                'id': 'ababa',
                'time': 1420092061,
                'timeNano': 14200920610000004000,
            },
            {
                'status': 'destroy',
                'from': 'example/db',
                'Type': 'container',
                'Actor': {
                    'ID': 'eeeee',
                    'Attributes': {
                        'com.docker.compose.project': 'test',
                        'com.docker.compose.service': 'db',
                        'image': 'example/db',
                        'name': 'test_db_1',
                    }
                },
                'id': 'eeeee',
                'time': 1420092061,
                'timeNano': 14200920610000004000,
            },
        ])

        def dt_with_microseconds(dt, us):
            return datetime.datetime.fromtimestamp(dt).replace(microsecond=us)

        def get_container(cid):
            if cid == 'eeeee':
                raise NotFound(None, None, "oops")
            if cid == 'abcde':
                name = 'web'
                labels = {LABEL_SERVICE: name}
            elif cid == 'ababa':
                name = 'db'
                labels = {LABEL_SERVICE: name}
            else:
                labels = {}
                name = ''
            return {
                'Id': cid,
                'Config': {'Labels': labels},
                'Name': '/project_%s_1' % name,
            }

        self.mock_client.inspect_container.side_effect = get_container

        events = project.events()

        events_list = list(events)
        # Assert the return value is a generator
        assert not list(events)
        assert events_list == [
            {
                'type': 'container',
                'service': 'web',
                'action': 'create',
                'id': 'abcde',
                'attributes': {
                    'name': 'test_web_1',
                    'image': 'example/image',
                },
                'time': dt_with_microseconds(1420092061, 2),
                'container': Container(None, get_container('abcde')),
            },
            {
                'type': 'container',
                'service': 'web',
                'action': 'attach',
                'id': 'abcde',
                'attributes': {
                    'name': 'test_web_1',
                    'image': 'example/image',
                },
                'time': dt_with_microseconds(1420092061, 3),
                'container': Container(None, get_container('abcde')),
            },
            {
                'type': 'container',
                'service': 'db',
                'action': 'create',
                'id': 'ababa',
                'attributes': {
                    'name': 'test_db_1',
                    'image': 'example/db',
                },
                'time': dt_with_microseconds(1420092061, 4),
                'container': Container(None, get_container('ababa')),
            },
            {
                'type': 'container',
                'service': 'db',
                'action': 'destroy',
                'id': 'eeeee',
                'attributes': {
                    'name': 'test_db_1',
                    'image': 'example/db',
                },
                'time': dt_with_microseconds(1420092061, 4),
                'container': None,
            },
        ]

    def test_net_unset(self):
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V1,
                services=[
                    {
                        'name': 'test',
                        'image': 'busybox:latest',
                    }
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        service = project.get_service('test')
        assert service.network_mode.id is None
        assert 'NetworkMode' not in service._get_container_host_config({})

    def test_use_net_from_container(self):
        container_id = 'aabbccddee'
        container_dict = dict(Name='aaa', Id=container_id)
        self.mock_client.inspect_container.return_value = container_dict
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'test',
                        'image': 'busybox:latest',
                        'network_mode': 'container:aaa'
                    },
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        service = project.get_service('test')
        assert service.network_mode.mode == 'container:' + container_id

    def test_use_net_from_service(self):
        container_name = 'test_aaa_1'
        self.mock_client.containers.return_value = [
            {
                "Name": container_name,
                "Names": [container_name],
                "Id": container_name,
                "Image": 'busybox:latest'
            }
        ]
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'aaa',
                        'image': 'busybox:latest'
                    },
                    {
                        'name': 'test',
                        'image': 'busybox:latest',
                        'network_mode': 'service:aaa'
                    },
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )

        service = project.get_service('test')
        assert service.network_mode.mode == 'container:' + container_name

    def test_uses_default_network_true(self):
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'foo',
                        'image': 'busybox:latest'
                    },
                ],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )

        assert 'default' in project.networks.networks

    def test_uses_default_network_false(self):
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[
                    {
                        'name': 'foo',
                        'image': 'busybox:latest',
                        'networks': {'custom': None}
                    },
                ],
                networks={'custom': {}},
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )

        assert 'default' not in project.networks.networks

    def test_container_without_name(self):
        self.mock_client.containers.return_value = [
            {'Image': 'busybox:latest', 'Id': '1', 'Name': '1'},
            {'Image': 'busybox:latest', 'Id': '2', 'Name': None},
            {'Image': 'busybox:latest', 'Id': '3'},
        ]
        self.mock_client.inspect_container.return_value = {
            'Id': '1',
            'Config': {
                'Labels': {
                    LABEL_SERVICE: 'web',
                },
            },
        }
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[{
                    'name': 'web',
                    'image': 'busybox:latest',
                }],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )
        assert [c.id for c in project.containers()] == ['1']

    def test_down_with_no_resources(self):
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[{
                    'name': 'web',
                    'image': 'busybox:latest',
                }],
                networks={'default': {}},
                volumes={'data': {}},
                secrets=None,
                configs=None,
            ),
        )
        self.mock_client.remove_network.side_effect = NotFound(None, None, 'oops')
        self.mock_client.remove_volume.side_effect = NotFound(None, None, 'oops')

        project.down(ImageType.all, True)
        self.mock_client.remove_image.assert_called_once_with("busybox:latest")

    def test_no_warning_on_stop(self):
        self.mock_client.info.return_value = {'Swarm': {'LocalNodeState': 'active'}}
        project = Project('composetest', [], self.mock_client)

        with mock.patch('compose.project.log') as fake_log:
            project.stop()
            assert fake_log.warn.call_count == 0

    def test_no_warning_in_normal_mode(self):
        self.mock_client.info.return_value = {'Swarm': {'LocalNodeState': 'inactive'}}
        project = Project('composetest', [], self.mock_client)

        with mock.patch('compose.project.log') as fake_log:
            project.up()
            assert fake_log.warn.call_count == 0

    def test_no_warning_with_no_swarm_info(self):
        self.mock_client.info.return_value = {}
        project = Project('composetest', [], self.mock_client)

        with mock.patch('compose.project.log') as fake_log:
            project.up()
            assert fake_log.warn.call_count == 0

    def test_no_such_service_unicode(self):
        assert NoSuchService('十六夜　咲夜'.encode('utf-8')).msg == 'No such service: 十六夜　咲夜'
        assert NoSuchService('十六夜　咲夜').msg == 'No such service: 十六夜　咲夜'

    def test_project_platform_value(self):
        service_config = {
            'name': 'web',
            'image': 'busybox:latest',
        }
        config_data = Config(
            version=V2_4, services=[service_config], networks={}, volumes={}, secrets=None, configs=None
        )

        project = Project.from_config(name='test', client=self.mock_client, config_data=config_data)
        assert project.get_service('web').platform is None

        project = Project.from_config(
            name='test', client=self.mock_client, config_data=config_data, default_platform='windows'
        )
        assert project.get_service('web').platform == 'windows'

        service_config['platform'] = 'linux/s390x'
        project = Project.from_config(name='test', client=self.mock_client, config_data=config_data)
        assert project.get_service('web').platform == 'linux/s390x'

        project = Project.from_config(
            name='test', client=self.mock_client, config_data=config_data, default_platform='windows'
        )
        assert project.get_service('web').platform == 'linux/s390x'

    @mock.patch('compose.parallel.ParallelStreamWriter._write_noansi')
    def test_error_parallel_pull(self, mock_write):
        project = Project.from_config(
            name='test',
            client=self.mock_client,
            config_data=Config(
                version=V2_0,
                services=[{
                    'name': 'web',
                    'image': 'busybox:latest',
                }],
                networks=None,
                volumes=None,
                secrets=None,
                configs=None,
            ),
        )

        self.mock_client.pull.side_effect = OperationFailedError('pull error')
        with pytest.raises(ProjectError):
            project.pull(parallel_pull=True)

        self.mock_client.pull.side_effect = OperationFailedError(b'pull error')
        with pytest.raises(ProjectError):
            project.pull(parallel_pull=True)

    def test_avoid_multiple_push(self):
        service_config_latest = {'image': 'busybox:latest', 'build': '.'}
        service_config_default = {'image': 'busybox', 'build': '.'}
        service_config_sha = {
            'image': 'busybox@sha256:38a203e1986cf79639cfb9b2e1d6e773de84002feea2d4eb006b52004ee8502d',
            'build': '.'
        }
        svc1 = Service('busy1', **service_config_latest)
        svc1_1 = Service('busy11', **service_config_latest)
        svc2 = Service('busy2', **service_config_default)
        svc2_1 = Service('busy21', **service_config_default)
        svc3 = Service('busy3', **service_config_sha)
        svc3_1 = Service('busy31', **service_config_sha)
        project = Project(
            'composetest', [svc1, svc1_1, svc2, svc2_1, svc3, svc3_1], self.mock_client
        )
        with mock.patch('compose.service.Service.push') as fake_push:
            project.push()
            assert fake_push.call_count == 2
