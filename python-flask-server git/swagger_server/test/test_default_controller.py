# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.sbf import SBF  # noqa: E501
from swagger_server.models.sbf_res import SBFRes  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_get_admin_by_id(self):
        """Test case for get_admin_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/admin',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_stations(self):
        """Test case for get_all_stations


        """
        response = self.client.open(
            '/api/station/all',
            method='POST',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_trains(self):
        """Test case for get_all_trains


        """
        response = self.client.open(
            '/api/train/all',
            method='POST',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_coffee(self):
        """Test case for get_coffee


        """
        response = self.client.open(
            '/api/coffee',
            method='POST',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_comp_env_by_id(self):
        """Test case for get_comp_env_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/compenv',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_cur_train_station_by_id(self):
        """Test case for get_cur_train_station_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/station',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_running_trains(self):
        """Test case for get_running_trains


        """
        response = self.client.open(
            '/api/train/running',
            method='POST',
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_cert_by_id(self):
        """Test case for get_station_cert_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/cert',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_dataset_by_id(self):
        """Test case for get_station_dataset_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/dataset',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_description_by_id(self):
        """Test case for get_station_description_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/description',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_errors_by_id(self):
        """Test case for get_station_errors_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/error',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_execenv_by_id(self):
        """Test case for get_station_execenv_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/execenv',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_finished_running_by_id(self):
        """Test case for get_station_finished_running_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train/finished/running',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_finished_transmission_by_id(self):
        """Test case for get_station_finished_transmission_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train/finished/transmission',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_info_by_id(self):
        """Test case for get_station_info_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/info',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_location_by_id(self):
        """Test case for get_station_location_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/location',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_log_by_id(self):
        """Test case for get_station_log_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/log',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_owner_by_id(self):
        """Test case for get_station_owner_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/owner',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_performance_by_id(self):
        """Test case for get_station_performance_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/performance',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_rejections_by_id(self):
        """Test case for get_station_rejections_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train/rejected',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_resp_by_id(self):
        """Test case for get_station_resp_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/responsible',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_rights_by_id(self):
        """Test case for get_station_rights_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/rights',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_started_running_by_id(self):
        """Test case for get_station_started_running_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train/started/running',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_station_title_by_id(self):
        """Test case for get_station_title_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/title',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_certificate_by_id(self):
        """Test case for get_train_certificate_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/cert',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_cpu_by_id(self):
        """Test case for get_train_cpu_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/performance/CPU',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_creator_by_id(self):
        """Test case for get_train_creator_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/creator',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_data_by_id(self):
        """Test case for get_train_data_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/expecteddata',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_description_by_id(self):
        """Test case for get_train_description_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/description',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_errors_by_id(self):
        """Test case for get_train_errors_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/error',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_finished_running_by_id(self):
        """Test case for get_train_finished_running_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/finished/running',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_finished_transmission_by_id(self):
        """Test case for get_train_finished_transmission_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/finished/transmission',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_future_route_by_id(self):
        """Test case for get_train_future_route_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/route/upcomming',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_info_by_id(self):
        """Test case for get_train_info_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/info',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_log_by_id(self):
        """Test case for get_train_log_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/log',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_memory_by_id(self):
        """Test case for get_train_memory_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/performance/memory',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_model_by_id(self):
        """Test case for get_train_model_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/model',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_past_route_by_id(self):
        """Test case for get_train_past_route_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/route/past',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_performance_by_id(self):
        """Test case for get_train_performance_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/performance',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_publisher_by_id(self):
        """Test case for get_train_publisher_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/publisher',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_rejections_by_id(self):
        """Test case for get_train_rejections_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/rejected',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_route_by_id(self):
        """Test case for get_train_route_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/route/full',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_title_by_id(self):
        """Test case for get_train_title_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/title',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_train_version_by_id(self):
        """Test case for get_train_version_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/train/version',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_trains_at_station_by_id(self):
        """Test case for get_trains_at_station_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_upcomming_trains_by_id(self):
        """Test case for get_upcomming_trains_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/station/train/upcomming}',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_by_id(self):
        """Test case for get_user_by_id


        """
        json_input = SBF()
        response = self.client.open(
            '/api/user',
            method='POST',
            data=json.dumps(json_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
