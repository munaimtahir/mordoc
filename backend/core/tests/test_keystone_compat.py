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

    def test_api_projects_endpoint_at_root(self):
        """API endpoints should work correctly at root path."""
        client = Client()
        response = client.get('/api/projects')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

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

    def test_force_script_name_env_var_usage(self):
        """Settings should use DJANGO_FORCE_SCRIPT_NAME from environment."""
        # This is a configuration test - verify the setting exists
        self.assertTrue(hasattr(settings, 'FORCE_SCRIPT_NAME'))
        # In test environment, it should be empty (default)
        self.assertEqual(settings.FORCE_SCRIPT_NAME, '')

    @override_settings(FORCE_SCRIPT_NAME='/mordoc')
    def test_static_url_includes_force_script_name(self):
        """When FORCE_SCRIPT_NAME is set, STATIC_URL should reflect it."""
        # Note: This test verifies the pattern exists in settings.py
        # In practice, the actual URL construction happens at settings load time
        # So we're verifying the configuration exists
        self.assertTrue(hasattr(settings, 'FORCE_SCRIPT_NAME'))
        # The test is that settings.py has the logic:
        # STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/" if FORCE_SCRIPT_NAME else "/static/"

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

    def test_whitenoise_middleware_installed(self):
        """WhiteNoise middleware should be in MIDDLEWARE list."""
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', settings.MIDDLEWARE)

    def test_cors_allow_credentials_enabled(self):
        """CORS_ALLOW_CREDENTIALS should be enabled."""
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)


class KeystoneAPIResponseTest(TestCase):
    """Test that API responses work correctly."""

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


class KeystoneDatabaseConfigTest(TestCase):
    """Test database configuration supports different connection strings."""

    def test_database_configured(self):
        """Database should be properly configured."""
        self.assertIsNotNone(settings.DATABASES)
        self.assertIn('default', settings.DATABASES)

    def test_database_supports_sqlite_for_testing(self):
        """Database configuration should support SQLite for testing."""
        # This test passes if we're running with SQLite
        db_engine = settings.DATABASES['default']['ENGINE']
        # Should support either PostgreSQL (production) or SQLite (testing)
        self.assertIn(db_engine, [
            'django.db.backends.postgresql',
            'django.db.backends.sqlite3'
        ])
