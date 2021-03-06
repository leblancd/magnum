# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Tests for manipulating Bays via the DB API"""

import six

from magnum.common import exception
from magnum.common import utils as magnum_utils
from magnum.tests.unit.db import base
from magnum.tests.unit.db import utils


class DbBayTestCase(base.DbTestCase):

    def test_create_bay(self):
        utils.create_test_bay()

    def test_create_bay_nullable_baymodel_id(self):
        utils.create_test_bay(baymodel_id=None)

    def test_create_bay_already_exists(self):
        utils.create_test_bay()
        self.assertRaises(exception.BayAlreadyExists,
                          utils.create_test_bay)

    def test_get_bay_by_id(self):
        bay = utils.create_test_bay()
        res = self.dbapi.get_bay_by_id(self.context, bay.id)
        self.assertEqual(bay.id, res.id)
        self.assertEqual(bay.uuid, res.uuid)

    def test_get_bay_by_name(self):
        bay = utils.create_test_bay()
        res = self.dbapi.get_bay_by_name(self.context, bay.name)
        self.assertEqual(bay.name, res.name)
        self.assertEqual(bay.uuid, res.uuid)

    def test_get_bay_by_uuid(self):
        bay = utils.create_test_bay()
        res = self.dbapi.get_bay_by_uuid(self.context, bay.uuid)
        self.assertEqual(bay.id, res.id)
        self.assertEqual(bay.uuid, res.uuid)

    def test_get_bay_that_does_not_exist(self):
        self.assertRaises(exception.BayNotFound,
                          self.dbapi.get_bay_by_id,
                          self.context, 999)
        self.assertRaises(exception.BayNotFound,
                          self.dbapi.get_bay_by_uuid,
                          self.context,
                          '12345678-9999-0000-aaaa-123456789012')

    def test_get_bay_list(self):
        uuids = []
        for i in range(1, 6):
            bay = utils.create_test_bay(uuid=magnum_utils.generate_uuid())
            uuids.append(six.text_type(bay['uuid']))
        res = self.dbapi.get_bay_list(self.context)
        res_uuids = [r.uuid for r in res]
        self.assertEqual(uuids.sort(), res_uuids.sort())

    def test_get_bay_list_with_filters(self):
        bm1 = utils.get_test_baymodel(id=1, uuid=magnum_utils.generate_uuid())
        bm2 = utils.get_test_baymodel(id=2, uuid=magnum_utils.generate_uuid())
        self.dbapi.create_baymodel(bm1)
        self.dbapi.create_baymodel(bm2)

        bay1 = utils.create_test_bay(
            name='bay-one',
            uuid=magnum_utils.generate_uuid(),
            baymodel_id=bm1['uuid'])
        bay2 = utils.create_test_bay(
            name='bay-two',
            uuid=magnum_utils.generate_uuid(),
            baymodel_id=bm2['uuid'],
            node_count=1)

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'baymodel_id': bm1['uuid']})
        self.assertEqual([bay1.id], [r.id for r in res])

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'baymodel_id': bm2['uuid']})
        self.assertEqual([bay2.id], [r.id for r in res])

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'name': 'bay-one'})
        self.assertEqual([bay1.id], [r.id for r in res])

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'name': 'bad-bay'})
        self.assertEqual([], [r.id for r in res])

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'node_count': 3})
        self.assertEqual([bay1.id], [r.id for r in res])

        res = self.dbapi.get_bay_list(self.context,
                                      filters={'node_count': 1})
        self.assertEqual([bay2.id], [r.id for r in res])

    def test_get_bay_list_baymodel_not_exist(self):
        utils.create_test_bay()
        self.assertEqual(1, len(self.dbapi.get_bay_list(self.context)))
        res = self.dbapi.get_bay_list(self.context, {
            'baymodel_id': magnum_utils.generate_uuid()})
        self.assertEqual(0, len(res))

    def test_destroy_bay(self):
        bay = utils.create_test_bay()
        self.assertIsNotNone(self.dbapi.get_bay_by_id(self.context,
                                                      bay.id))
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.BayNotFound,
                          self.dbapi.get_bay_by_id,
                          self.context, bay.id)

    def test_destroy_bay_by_uuid(self):
        bay = utils.create_test_bay()
        self.assertIsNotNone(self.dbapi.get_bay_by_uuid(self.context,
                                                        bay.uuid))
        self.dbapi.destroy_bay(bay.uuid)
        self.assertRaises(exception.BayNotFound,
                          self.dbapi.get_bay_by_uuid, self.context,
                          bay.uuid)

    def test_destroy_bay_that_does_not_exist(self):
        self.assertRaises(exception.BayNotFound,
                          self.dbapi.destroy_bay,
                          '12345678-9999-0000-aaaa-123456789012')

    def test_destroy_bay_that_has_pods(self):
        bay = utils.create_test_bay()
        pod = utils.create_test_pod(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, pod.bay_uuid)
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.PodNotFound,
                          self.dbapi.get_pod_by_id, self.context, pod.id)

    def test_destroy_bay_that_has_pods_by_uuid(self):
        bay = utils.create_test_bay()
        pod = utils.create_test_pod(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, pod.bay_uuid)
        self.dbapi.destroy_bay(bay.uuid)
        self.assertRaises(exception.PodNotFound,
                          self.dbapi.get_pod_by_id, self.context, pod.id)

    def test_destroy_bay_that_has_services(self):
        bay = utils.create_test_bay()
        service = utils.create_test_service(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, service.bay_uuid)
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.ServiceNotFound,
                          self.dbapi.get_service_by_id,
                          self.context, service.id)

    def test_destroy_bay_that_has_services_by_uuid(self):
        bay = utils.create_test_bay()
        service = utils.create_test_service(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, service.bay_uuid)
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.ServiceNotFound,
                          self.dbapi.get_service_by_id,
                          self.context, service.id)

    def test_destroy_bay_that_has_rc(self):
        bay = utils.create_test_bay()
        rc = utils.create_test_rc(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, rc.bay_uuid)
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.ReplicationControllerNotFound,
                          self.dbapi.get_rc_by_id,
                          self.context, rc.id)

    def test_destroy_bay_that_has_rc_by_uuid(self):
        bay = utils.create_test_bay()
        rc = utils.create_test_rc(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, rc.bay_uuid)
        self.dbapi.destroy_bay(bay.uuid)
        self.assertRaises(exception.ReplicationControllerNotFound,
                          self.dbapi.get_rc_by_id,
                          self.context, rc.id)

    def test_destroy_bay_that_has_containers(self):
        bay = utils.create_test_bay()
        container = utils.create_test_container(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, container.bay_uuid)
        self.dbapi.destroy_bay(bay.id)
        self.assertRaises(exception.ContainerNotFound,
                          self.dbapi.get_container_by_id,
                          self.context, container.id)

    def test_destroy_bay_that_has_containers_by_uuid(self):
        bay = utils.create_test_bay()
        container = utils.create_test_container(bay_uuid=bay.uuid)
        self.assertEqual(bay.uuid, container.bay_uuid)
        self.dbapi.destroy_bay(bay.uuid)
        self.assertRaises(exception.ContainerNotFound,
                          self.dbapi.get_container_by_id,
                          self.context, container.id)

    def test_update_bay(self):
        bay = utils.create_test_bay()
        old_nc = bay.node_count
        new_nc = 5
        self.assertNotEqual(old_nc, new_nc)
        res = self.dbapi.update_bay(bay.id, {'node_count': new_nc})
        self.assertEqual(new_nc, res.node_count)

    def test_update_bay_not_found(self):
        bay_uuid = magnum_utils.generate_uuid()
        self.assertRaises(exception.BayNotFound, self.dbapi.update_bay,
                          bay_uuid, {'node_count': 5})

    def test_update_bay_uuid(self):
        bay = utils.create_test_bay()
        self.assertRaises(exception.InvalidParameterValue,
                          self.dbapi.update_bay, bay.id,
                          {'uuid': ''})
