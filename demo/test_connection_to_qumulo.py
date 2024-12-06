from requests.sessions import Session
from requests.exceptions import SSLError

try:
    session = Session()
    session.headers = {"content-type": "application/json"}
    session.auth = ("ACCOUNTS\\RIS-SVC-CDFNT-QUMULO", 'dhv]$ML5RJx)T&6fmBU@yHK";')

    response = session.get('https://storage2-dev.ris.wustl.edu:8000')
except SSLError as e:
    print(f"SSL Error: {e}")
