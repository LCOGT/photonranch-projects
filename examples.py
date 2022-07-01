"""Refer to this file for example Python requests handled
at the photonranch-projects API endpoints.

All endpoints are handled at the base API URL
"https://projects.photonranch.org/{stage}",
here {stage} is the development stage in [test, dev, prod].

All projects endpoints:
/new-project
/modify-project
/get-project
/add-project-data
/add-project-event
/delete-project
/get-all-projects
/get-user-projects

For more details, refer to this repository's README.
"""

import requests, json


# Demonstrate the add-project-data endpoint, which adds a newly
# taken exposure to the details of a project, in order to track
# the project's completion progress.
def addProjectData():
    
    url = "https://projects.photonranch.org/dev/add-project-data"
    request_body = json.dumps({

        # A project is uniquely specified by the pair of values: 
        # project_name and created_at. 
        "project_name": "m101",
        "created_at": "2020-06-24T16:53:56Z",

        # Currently, a project can only have one target,
        # so this value should always be zero.
        # "target_index": 0,

        # Specify which exposure request is being added to the project data.
        "exposure_index": 0,
        "base_filename": "filename_abc"
    })

    response = requests.post(url, request_body)
    print(response.json()) 


# The get-project endpoint retrieves the details of
# a specified project from the DynamoDB table at AWS.
def getProject(): 
    url = "https://projects.photonranch.org/dev/get-project"
    request_body = json.dumps({
        "project_name": "m101",
        "created_at": "2020-06-24T16:53:56Z",
    })
    response = requests.post(url, request_body).json()
    print(json.dumps(response, indent=2))


# The get-all-projects endpoint retrieves the details of
# all existing projects in the table.
def getAllProjects(): 
    url = "https://projects.photonranch.org/dev/get-all-projects"
    response = requests.post(url).json()
    print(json.dumps(response, indent=2))

# The add-project-event endpoint associates an existing project
# to a calendar reservation.
def addProjectEvent():
    url = "https://projects.photonranch.org/dev/add-project-event"
    request_body = json.dumps({
        "project_name": "m101",
        "created_at": "2020-06-24T16:53:56Z",
        # Id of the calendar event we want to add to.
        # This id is made up, but event ids follow this format.
        "event_id": "f83y1313-23f8-xxxx-zzzz-yy1351b7a711"
    })


if __name__=="__main__":

    #getProject()
    #getAllProjects()

    import requests, time
    url = "https://api.photonranch.org/api/weather/write"
    #print(requests.post(url).json())

    data = json.dumps({
        "weatherData": {
            "calc_HSI_lux": 0.002,
            "calc_sky_mpsas": 1.99,
            "dewpoint_C": -3.3,
            "humidity_%": 50,
            "last_sky_update_s": 5,
            "meas_sky_mpsas": 1.9,
            "open_ok": "Yes",
            "pressure_mbar": 784.0,
            "rain_rate": 0,
            "sky_temp_C": -36,
            "solar_flux_w/m^2": "NA",
            "temperature_C": 25,
            "wind_m/s": 3,
            "wx_ok": "Yes"
        },
        "site": "tst",
        "timestamp_s": int(time.time())
    })

    print(requests.post(url, data))

