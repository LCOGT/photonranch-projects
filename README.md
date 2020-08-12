# photonranch-projects

*Note: this is a temporary info dump (copied from a slack message) that I thought was worth saving. But an actual readme-type overview is still due.*

---

Two python snippets demonstrating code for observatories to get tasks to do:

The first snippet gets all projects. At some point, I’ll make it so you can filter by various conditions (only get unfinished projects, etc). Currently, projects are not linked to any specific site, but that might be a future feature too.

```python
import requests
url = "https://projects.photonranch.org/dev/get-all-projects"
all_projects = requests.post(url).json()
```

This next snippet returns all calendar reservations for a site within the given start and end times (UTC).

```python
import requests, json
url = "https://calendar.photonranch.org/dev/siteevents"
body = json.dumps({
    "site": "saf",             
    # Get events that end between these two UTC times.             
    "start": "2020-06-01T01:00:00Z",
    "end": "2020-06-02T01:00:00Z",            
    # optional: adds the full project to any events that have them. Not including this in the request means you get the project_id only, no details. 
    "full_project_details": True        
})
events = requests.post(url, body).json()
```

My thinking is that each afternoon a site can fetch the reservations for that night, and make sure to fulfill them (either working on the associated project and/or prioritizing the user who owns the reservation). The observatory can also fetch incomplete projects, and work on any of them during idle time. I will be adding ways to update the completion of a project as images are taken and uploaded.

---

Here is an endpoint for your code (the observatory) to update AWS when new data for a project has been completed. Sending this request will do the following to a project:
decrement the remaining exposure count
add the completed filename to the list of available project data.

I think the best time to send this update is after all the data has been uploaded.
Here's an example of how you might send the update. Feel free to tailor it to your workflow:

```python
import requests, json
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
# this should work in any python3 environment
```

To elaborate further on what the request_body values mean:
- project_name and created_at are both found directly in the project definition. They are used in tandem as a unique identifier for the database.
- target_index is the index of the target that was captured with the new data at hand. The project definition will include an array of one or more targets. For example, if a project asks for project_targets=[{name: m1, ...}, {name: m2, ...}] and we just finished capturing an image of m2, then the "target_index" will have the value of 1, since project_targets[1] == {name: m2, ...}.
- exposure_index is similar to target_index: the value is the array index that specifies the exposure that was taken.
- base_filename is the filename that is common to all formats of the same data. Something like saf-sq01-20200623-00000299 (without the EX** or .file_extension).