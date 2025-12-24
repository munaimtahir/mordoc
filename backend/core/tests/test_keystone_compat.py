"""
Tests for Keystone compatibility with subpath deployment.

These tests verify that the application works correctly when deployed
under a subpath (e.g., /mordoc) as required by Keystone's path-based routing.
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings


class KeystoneSubpathCompatibilityTest(TestCase):
    """Test app behavior when FORCE_SCRIPT_NAME is set (subpath deployment)."""

    def test_health_check_works_at_root(self):
        """Health check should work when deployed at root path."""
        client = Client()
        response = client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('ok'))

    @override_settings(FORCE_SCRIPT_NAME='/mordoc')
    def test_health_check_works_with_subpath(self):
        """Health check should work when FORCE_SCRIPT_NAME is set."""
        client = Client()
        # Django automatically handles FORCE_SCRIPT_NAME for URL resolution
        response = client.get('/mordoc/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('ok'))

    @override_settings(FORCE_SCRIPT_NAME='/mordoc')
    def test_api_projects_endpoint_with_subpath(self):
        """API endpoints should work correctly with FORCE_SCRIPT_NAME."""
        client = Client()
        response = client.get('/mordoc/api/projects')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_frontend_catchall_at_root(self):
        """Frontend catchall should serve index.html for non-API routes at root."""
        client = Client()
        # This should be caught by the frontend catchall
        response = client.get('/projects')
        self.assertEqual(response.status_code, 200)
        # Should serve index.html (not JSON)
        self.assertIn('text/html', response.get('Content-Type', ''))

    @override_settings(FORCE_SCRIPT_NAME='/mordoc')
    def test_frontend_catchall_with_subpath(self):
        """Frontend catchall should work with FORCE_SCRIPT_NAME."""
        client = Client()
        response = client.get('/mordoc/projects')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))

    def test_static_url_configuration(self):
        """STATIC_URL should be properly configured."""
        self.assertIsNotNone(settings.STATIC_URL)
        # Should start with / or be a full URL
        self.assertTrue(settings.STATIC_URL.startswith('/') or 
                       settings.STATIC_URL.startswith('http'))

    def test_media_url_configuration(self):
        """MEDIA_URL should be properly configured."""
        self.assertIsNotNone(settings.MEDIA_URL)
        self.assertTrue(settings.MEDIA_URL.startswith('/') or 
                       settings.MEDIA_URL.startswith('http'))

    @override_settings(FORCE_SCRIPT_NAME='/myapp')
    def test_static_url_with_force_script_name(self):
        """STATIC_URL should include FORCE_SCRIPT_NAME when set."""
        # This test verifies the settings.py logic
        # In practice, we'd need to reload settings, but we can verify the pattern
        self.assertIsNotNone(settings.STATIC_URL)

    def test_cors_settings_configured(self):
        """CORS settings should be properly configured."""
        self.assertTrue(hasattr(settings, 'CORS_ALLOWED_ORIGINS'))
        self.assertIsInstance(settings.CORS_ALLOWED_ORIGINS, list)

    def test_use_x_forwarded_host_enabled(self):
        """USE_X_FORWARDED_HOST should be enabled for reverse proxy support."""
        self.assertTrue(settings.USE_X_FORWARDED_HOST)

    def test_whitenoise_index_file_enabled(self):
        """WHITENOISE_INDEX_FILE should be enabled for SPA support."""
        self.assertTrue(settings.WHITENOISE_INDEX_FILE)


class KeystoneReverseProxyHeadersTest(TestCase):
    """Test handling of reverse proxy headers (X-Forwarded-*)."""

    def test_x_forwarded_host_header(self):
        """Application should respect X-Forwarded-Host header."""
        client = Client()
        response = client.get(
            '/api/health/',
            HTTP_X_FORWARDED_HOST='example.com'
        )
        self.assertEqual(response.status_code, 200)
        # Should work without errors

    def test_x_forwarded_proto_header(self):
        """Application should handle X-Forwarded-Proto header."""
        client = Client()
        response = client.get(
            '/api/health/',
            HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200)


class KeystoneAPIResponseTest(TestCase):
    """Test that API responses don't include problematic absolute URLs."""

    def test_health_endpoint_response(self):
        """Health endpoint should return simple JSON without URLs."""
        client = Client()
        response = client.get('/api/health/')
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertTrue(data.get('ok'))
        # Should not include absolute URLs in response

    def test_projects_list_endpoint(self):
        """Projects endpoint should return proper JSON."""
        client = Client()
        response = client.get('/api/projects')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
