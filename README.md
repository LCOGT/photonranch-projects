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

## Updating Projects with Completed Data


Projects are designed to store not only the request details, but also pointers to completed images and completion status. 

In order for this model to work, the site that completes an image for a project request should send the appropriate metadata using the projects api. 

### Example Code

First, here is an example request that illustrates what the update looks like. Note there are five pieces of data that need to be included:
- project_name
- created_at
- target_index
- exposure_index
- base_filename

The code will be followed by explanations of these values. 


```python
import requests, json


# A project is uniquely specified by the pair of values: project_name and created_at. 
project_name = "tim test project"
created_at = "2020-12-17T01:26:10Z"

# Specifies which exposure request the image fulfills
target_index = 0

# Always 0 (multiple targets are not currently supported)
exposure_index = 0

base_filename = "file-blue-1"
    
    
# Compile and send the complete request.
url = "https://projects.photonranch.org/dev/add-project-data"
request_body = json.dumps({
    "project_name": project_name,
    "created_at": created_at,
    "target_index": target_index,
    "exposure_index": exposure_index,
    "base_filename": base_filename,
})
#response = requests.post(url, request_body)
#print(response.json())

```

### Parameter Details

#### project_name, created_at

Projects are uniquely identified by the combination of their name and creation date. You should have these values already if the site has chosen a project to work on. 

#### exposure_index

Here is how the project stores requested exposures and completed exposures:

```
  ...
  "remaining": [
    2,
    3
  ],
  "project_data": [
    [], # no blue images taken yet
    ["base-filename-for-red-image"] # one red image completed already
  ],
  "exposures": [
    {
      "filter": "Blue",
      "area": "FULL",
      "exposure": 1,
      "dither": "no",
      "bin": "2, 2",
      "count": "2",
      "photometry": "-",
      "imtype": "light",
      "defocus": 0
    },
    {
      "filter": "Red",
      "area": "FULL",
      "exposure": 1,
      "dither": "no",
      "bin": "2, 2",
      "count": "4",
      "photometry": "-",
      "imtype": "light",
      "defocus": 0
    }
  ],
  ...
  ```
  
The exposure_index value specifies which of the multiple requested exposures was used for the completed file.
  
For example, if the image was an exposure with the red filter, the exposure index would be 1 (corresponding to the second item in the 'exposures' list). Once the request goes through, the appropriate list in 'project_data' would show the new filename. 
  

#### target_index

When projects used to support multiple targets, the target index behaved like the exposure index, and the project_data had one more level of nesting (files would save at `project_data[target_index][exposure_index]`).

However, we opted to remove multi-target capabilities, so target_index is always 0. 

target_index has not been removed because we have plans to add multi-target support back to projects. 

#### base_filename

This is the general filename that is used to get the images completed in a project. The format is something like:

`wmd-sq01-20201216-00001675`

with a reminder that this should not include the EX00 value or the .fits file extensions. 

### Example Full Project

For reference, this is what a full project looks like. 

```json
{
  "user_id": "google-oauth2|100354044221813550027",
  "project_constraints": {
    "meridian_flip": "flip_ok",
    "dec_offset_units": "deg",
    "close_on_block_completion": false,
    "site_tags": [
      "wmd"
    ],
    "prefer_bessell": false,
    "frequent_autofocus": false,
    "ra_offset": 0,
    "lunar_phase_max": 60,
    "lunar_dist_min": 30,
    "max_airmass": 2,
    "enhance_photometry": false,
    "dec_offset": 0,
    "max_ha": 4,
    "ra_offset_units": "deg",
    "near_tycho_star": false,
    "position_angle": 0
  },
  "project_name": "tim test project",
  "scheduled_with_events": [],
  "created_at": "2020-12-17T01:26:10Z",
  "remaining": [
    0,
    1
  ],
  "project_note": "for adding data",
  "project_data": [
    [
      "file-blue-1",
      "file-blue-1"
    ],
    [
      "file-red-1",
      "file-red-1",
      "file-red-1"
    ]
  ],
  "exposures": [
    {
      "filter": "Blue",
      "area": "FULL",
      "exposure": 1,
      "dither": "no",
      "bin": "2, 2",
      "count": "2",
      "photometry": "-",
      "imtype": "light",
      "defocus": 0
    },
    {
      "filter": "Red",
      "area": "FULL",
      "exposure": 1,
      "dither": "no",
      "bin": "2, 2",
      "count": "4",
      "photometry": "-",
      "imtype": "light",
      "defocus": 0
    }
  ],
  "project_targets": [
    {
      "name": "M 1",
      "ra": "5.5755",
      "dec": "22.0145"
    }
  ]
}
```
