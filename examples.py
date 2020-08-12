import requests, json

# Demonstrate add-project-data endpoint

def addProjectData():
    url = "https://projects.photonranch.org/dev/add-project-data"
    request_body = json.dumps({

        # A project is uniquely specified by the pair of values: project_name and created_at. 
        "project_name": "m101",
        "created_at": "2020-06-24T16:53:56Z",

        # A project definition will have one or more targets listed in an array. 
        # Specify which target was captured in the data we are adding.
        "target_index": 0,

        # Similarly, we specify which exposure request is being added.
        "exposure_index": 0,

        "base_filename": "filename_abc"
    })

    response = requests.post(url, request_body)
    print(response.json()) 

def getProject(): 
    url = "https://projects.photonranch.org/dev/get-project"
    request_body = json.dumps({
        "project_name": "m101",
        "created_at": "2020-06-24T16:53:56Z",
    })
    response = requests.post(url, request_body).json()
    print(json.dumps(response, indent=2))

def getAllProjects(): 
    url = "https://projects.photonranch.org/dev/get-all-projects"
    response = requests.post(url).json()
    print(json.dumps(response, indent=2))



if __name__=="__main__":

    #getProject()
    #getAllProjects()

    #s = Solution()
    #s.lengthOfLongestSubstring(s1)
    #s.lengthOfLongestSubstring(s2)
    #s.lengthOfLongestSubstring(s3)
    #s.lengthOfLongestSubstring(s4)

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

