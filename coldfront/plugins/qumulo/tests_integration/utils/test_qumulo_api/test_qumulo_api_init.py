from django.test import TestCase, tag
from coldfront.plugins.qumulo.utils.qumulo_api import QumuloAPI
import os


class TestQumuloApiInit(TestCase):
    @tag("integration")
    def test_logs_in_without_throwing_error(self):
        try:
            qumulo_api = QumuloAPI()
        except:
            self.fail("Login failed!")
        
    # INCOMPLETE, needs environment variables set
    @tag("integration")    
    def test_logs_into_specific_server(self):
        host = os.environ.get("QUMULO_TEST_HOST")
        port = os.environ.get("QUMULO_TEST_PORT")
        username = os.environ.get("QUMULO_TEST_USER")
        password = os.environ.get("QUMULO_TEST_PASS")
        
        try:
            qumulo_api = QumuloAPI(
                host=host, port=port, username=username, password=password
            )
        except:
            self.fail("Login failed!")

    
    #INCOMPLETE
    @tag("integration")
    def test_can_have_2_connections(self):
        host = os.environ.get("QUMULO_TEST_HOST")
        port = os.environ.get("QUMULO_TEST_PORT")
        username = os.environ.get("QUMULO_TEST_USER")
        password = os.environ.get("QUMULO_TEST_PASS")
        
        try:
            default_qumulo_api = QumuloAPI()
        except:
            self.fail("Login failed!")
            
        try:
            custom_qumulo_api = QumuloAPI(
                host=host, port=port, username=username, password=password
            )
        except:
            self.fail("Login failed!")
            
        # do basic call to asssert they are different instances
        
