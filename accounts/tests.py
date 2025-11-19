from django.test import TestCase
from django.urls import reverse

class AccountsLoginTests(TestCase):
    def test_post_invalid_credentials_shows_error(self):
        url = reverse('accounts:signin')
        response = self.client.post(url, data={'email': 'no@existe.com', 'password': 'badpass'})
        # Should render the sign in page with error, not raise exception
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Correo o contraseña incorrectos.')

