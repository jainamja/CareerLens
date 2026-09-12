from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class HealthCheckTests(APITestCase):
    def test_health_check(self):
        """
        Ensure health check endpoint returns 200 OK.
        """
        url = reverse('v1:health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})
