from django.test import LiveServerTestCase
from selenium import webdriver


class UITest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Firefox()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_homepage_title(self):
        self.browser.get(self.live_server_url)
        self.assertIn('Videoverhandlungen an deutschen Gerichten | Seite 1 - Videoverhandlung.de', self.browser.title)
