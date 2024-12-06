import requests


class RESTClient:
    def __init__(self):
        self.base_url = "http://localhost:3000/rest/attr/info/service_provision?"

    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()

    def post(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    # Add other methods like put, patch, delete as needed


# Example usage:
# client = RESTClient("https://api.example.com/")
# data = client.get("/users")
# print(data)

# curl -v -H "x-remote-user: sleong" -H "Content-Type:application/json" 'http://localhost:3000/rest/attr/info/service_provision?attribute=name,metric,amount,provision_usage_creation_date&amp;filter=\{"name":"compute-ris","metric":"slot","provision_usage_creation_date":"2021-05-01"\}'
# curl -v -H "x-remote-user: sleong" -H "Content-Type:application/json" 'http://localhost:3000/rest/attr/info/service_provision?attribute=id,service_id,name,sponsor,department_number,department_name,funding_number,billing_contact,technical_contact,secure,service_desk_ticket_number,audit,creation_timestamp,billing_startdate,status,sponsor_department_number,fileset_name,fileset_alias,exempt,service_rate_category,comment,billing_cycle,subsidized,quota,allow_nonfaculty,acl_group_members,who,parent_id,is_condo_group,sla&filter=\{"fileset_alias":"jin810_active"\}'
