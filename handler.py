import json
import os
import boto3
import decimal
import requests

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')

projects_table = os.environ['PROJECTS_TABLE']


#=========================================#
#=======     Helper Functions     ========#
#=========================================#

def create_response(statusCode, message):
    return { 
        'statusCode': statusCode,
        'headers': {
            # Required for CORS support to work
            'Access-Control-Allow-Origin': '*',
            # Required for cookies, authorization headers with HTTPS
            'Access-Control-Allow-Credentials': 'true',
        },
        'body': message
    }

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, decimal.Decimal):
            if o % 1 != 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def removeProjectFromCalendarEvents(list_of_event_ids):
    # The stage is used in some URLs. The production URL for the calendar
    # is '...org/calendar...', so check first if the stage is 'prod'.
    if os.environ['STAGE'] == 'prod':
        stage = 'calendar'
    else:
        stage = os.environ['STAGE']
    calendarURL = f"https://calendar.photonranch.org/{stage}/remove-project-from-events"
    requestBody = json.dumps({
        "events": list_of_event_ids
    })
    requests.post(calendarURL, requestBody)


#=========================================#
#=======       Core Methods       ========#
#=========================================#
    
def modify_project(project_name: str, created_at: str, project_changes: dict):
    """
    Modify an exising project.

    Args:
        project_name (str): name of the existing project we want to modify.
        created_at (str): utc iso datetime of project creation, used to id 
            the existing project we want to modify.
        project_changes (dict): these are the changes we want to apply. The 
            format of this dict should be the same as if we were adding a new
            project.

    Returns:
        dict: contains the following keys:
            is_successful (bool): whether or not the update worked
            description (str): optional text to display to the user
            updated_project (str): the state of the project after the update.
    """

    table = dynamodb.Table(projects_table)

    old_project = get_project(project_name, created_at)

    # If the project specified by project_name and created_at is not found:
    if not old_project["project_exists"]: 
        return {
            "is_successful": False,
            "description": "The requested project does not exist.",
            "updated_project": []
        }

    # Initialize the dict that will overwrite the existing project in dynamodb.
    updated_project = old_project["project"]

    # Apply the new project changes we want to make
    updated_project["project_constraints"] = project_changes["project_constraints"]
    updated_project["project_name"] = project_changes["project_name"]
    updated_project["project_note"] = project_changes["project_note"]
    updated_project["project_targets"] = project_changes["project_targets"]
    updated_project["project_sites"] = project_changes["project_sites"]
    updated_project["scheduled_with_events"] = project_changes["scheduled_with_events"]

    # A tricky detail is how to keep track of existing project data for 
    # exposure requests that have been modified. 

    # Note: this treats identical exposure requests with different image counts 
    # as different reqeusts. In other words, editing a project by increasing the
    # number of images for some exposure will start from scratch, ignoring 
    # any previously gathered data. 

    # initialize a new array to store identifiers for completed project data
    updated_project_data = [[] for x in range(len(project_changes["exposures"]))]
    updated_remaining_data = [exposure["count"] for exposure in project_changes["exposures"]]

    # For each exposure request, try to match it with an existing exposure 
    # request. If they match, then 'import' the associated data into the 
    # updated_project_data array. 
    for new_index, new_exposure in enumerate(project_changes["exposures"]):
        for old_index, old_exposure in enumerate(old_project["project"]["exposures"]):
            if new_exposure == old_exposure: 
                updated_project_data[new_index] = old_project["project"]["project_data"][old_index]
                updated_remaining_data[new_index] = old_project["project"]["remaining"][old_index]
                break                   

    # Finally, add the updated_project_data array to the udpated_project dict.
    updated_project["project_data"] = updated_project_data
    updated_project["remaining"] = updated_remaining_data
    updated_project["exposures"] = project_changes["exposures"]

    # Delete the existing project from the table
    table.delete_item(
        Key={
            "project_name": project_name,
            "created_at": created_at
        },
    )
    # Add the updated project back
    dynamodb_entry = json.loads(json.dumps(updated_project, cls=DecimalEncoder), parse_float=decimal.Decimal)
    table_response = table.put_item(Item=dynamodb_entry)
    return {
        "is_successful": True,
        "description": "Project has been updated.",
        "updated_project": table_response,
    }
        
    

def get_project(project_name, created_at):
    table = dynamodb.Table(projects_table)

    response = table.get_item(
        Key={
            "project_name": project_name,
            "created_at": created_at,
        }
    )
    if 'Item' in response:
        return {
            "project_exists": True,
            "project": response['Item']
        }
    else: 
        return {
            "project_exists": False,
            "project": []
        }


#=========================================#
#=======          Handlers        ========#
#=========================================#
def addNewProject(event, context):
    
    event_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)

    print("event_body:")
    print(event_body)

    # Check that all required keys are present.
    required_keys = ['project_name', 'user_id', 'created_at']
    actual_keys = event_body.keys()
    for key in required_keys:
        if key not in actual_keys:
            print(f"Error: missing requied key {key}")
            return {
                "statusCode": 400,
                "body": f"Error: missing required key {key}",
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true",
                },
            }

    # Convert floats into decimals for dynamodb
    dynamodb_entry = json.loads(json.dumps(event_body), parse_float=decimal.Decimal)

    table_response = table.put_item(Item=dynamodb_entry)

    message = json.dumps({
        'table_response': table_response,
        'new_project': event_body,
    })
    return create_response(200, message)

def modify_project_handler(event, context):

    table = dynamodb.Table(projects_table)
    event_body = json.loads(event.get("body", ""))
    print(event_body)

    project_name = event_body['project_name']
    created_at = event_body['created_at']
    project_changes = event_body['project_changes']

    response = modify_project(project_name, created_at, project_changes)
    return create_response(200, json.dumps(response, cls=DecimalEncoder))


def get_project_handler(event, context):

    event_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)

    print("event_body:")
    print(event_body)

    project_name = event_body['project_name']
    created_at = event_body['created_at']

    project = get_project(project_name, created_at)
    if project["project_exists"]:
        project_json = json.dumps(project["project"], cls=DecimalEncoder)
        return create_response(200, project_json)
    else: 
        return create_response(404, "Project not found.")

def getAllProjects(event, context):
    '''
    example python code that uses this endpoint:

        import requests
        url = "https://projects.photonranch.org/dev/get-all-projects"
        all_projects = requests.post(url).json()
    '''

    table = dynamodb.Table(projects_table)

    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return create_response(200, json.dumps(data, cls=DecimalEncoder))


def getUserProjects(event, context):

    event_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)

    print("event_body:")
    print(event_body)

    # Check that all required keys are present.
    required_keys = ['user_id']
    actual_keys = event_body.keys()
    for key in required_keys:
        if key not in actual_keys:
            print(f"Error: missing requied key {key}")
            return {
                "statusCode": 400,
                "body": f"Error: missing required key {key}",
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true",
                },
            }

    response = table.query(
        IndexName="userid-createdat-index",
        KeyConditionExpression=Key('user_id').eq(event_body['user_id'])
    )
    print(response)
    user_projects = json.dumps(response['Items'], cls=DecimalEncoder)

    return create_response(200, user_projects)


def addProjectEvent(event, context):
    '''
    Projects keep a list of events that they are scheduled with. 
    This way, if a project is deleted, it can be removed from any associated events.

    This method will add the provided event to the project's list of events.

    We could use a set in dynamodb to keep track of associated events. But that
    gets complicated because JSON does not support sets, so we would need lots
    of custom modifier code throughout the pipeline. 

    Instead we'll keep it simple with a list. Get the list, check if already 
    contains our event, and add it if not, then update dynamodb. 
    '''

    request_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)

    print("event_body:")
    print(request_body)

    project_name = request_body["project_name"]
    created_at = request_body["created_at"]
    event_id = request_body["event_id"] # ID of the calendar event

    response = table.get_item(
        Key={
            "project_name": project_name,
            "created_at": created_at
        },
    )
    events_list = response['Item']['scheduled_with_events']

    # Don't add a duplicate
    if event_id in events_list:
        return create_response(200, 'Event already associated with this project')

    # Add the event to the list and then update the project in dynamodb
    else:
        events_list.append(event_id)
        print(f"events_list: {events_list}")

        update_response = table.update_item(
            Key={
                "project_name": project_name,
                "created_at": created_at,
            },
            UpdateExpression="SET scheduled_with_events = :swe",
            ExpressionAttributeValues={
                ":swe": events_list
            }
        )
        return create_response(200, 'Successfully associated event with project.')


def addProjectData(event, context):
    '''
    When an observatory captures and uploads an image requested in a project,
    it should use this endpoint to update the projects completion status.
    '''

    event_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)
    #table = dynamodb.Table("photonranch-projects")

    print("event")
    print(json.dumps(event))

    # unique project identifier
    project_name = event_body["project_name"]
    created_at = event_body["created_at"]

    # Indices for where to save the new data in project_data
    exposure_index = event_body["exposure_index"]

    # Data to save
    base_filename = event_body["base_filename"]


    # First, get the 'project_data' and 'remaining' arrays we want to update
    # 'project_data[exposure_index]' stores filenames of completed exposures
    # 'remaining[exposure_index[' is the number of exposures remaining
    resp1 = table.get_item(
        Key={
            "project_name": project_name,
            "created_at": created_at,
        }
    ) 
    project_data = resp1["Item"]["project_data"]
    remaining = resp1["Item"]["remaining"]

    # Next, add our new information
    project_data[exposure_index].append(base_filename)
    remaining[exposure_index] = int(remaining[exposure_index]) - 1

    print("updated values: ")
    print(project_data)
    print(remaining)
    
    # Finally, update the dynamodb project entry with the revised 'project_data' and 'remaining'
    resp2 = table.update_item(
        Key={
            "project_name": project_name,
            "created_at": created_at,
        },
        UpdateExpression="SET #project_data = :project_data_updated, #remaining = :remaining_updated",
        ExpressionAttributeNames={
            "#project_data": "project_data",
            "#remaining": "remaining",
        },
        ExpressionAttributeValues={
            ":project_data_updated": project_data,
            ":remaining_updated": remaining,
        }
    )
    if resp2["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return create_response(200, json.dumps({"message": "success"}))
    else:
        return create_response(500, json.dumps({"message": "failed to update project in dynamodb"}))


def deleteProject(event, context):

    request_body = json.loads(event.get("body", ""))
    table = dynamodb.Table(projects_table)

    print("event")
    print(json.dumps(event))

    # Get the user's roles provided by the lambda authorizer
    userMakingThisRequest = event["requestContext"]["authorizer"]["principalId"]
    print(f"userMakingThisRequest: {userMakingThisRequest}")
    userRoles = json.loads(event["requestContext"]["authorizer"]["userRoles"])
    print(f"userRoles: {userRoles}")

    # Check if the requester is an admin
    requesterIsAdmin="false"
    if 'admin' in userRoles:
        requesterIsAdmin="true"
    print(f"requesterIsAdmin: {requesterIsAdmin}")

    # Specify the event with our pk (project_name) and sk (created_at)
    project_name = request_body['project_name']
    created_at = request_body['created_at']

    # Get the project we want to delete so we can remove it from all its
    # scheduled calendar events.
    event_response = table.get_item(
        Key={
            "project_name": project_name,
            "created_at": created_at
        },
    )
    associated_events = event_response['Item']['scheduled_with_events']

    # Don't remove project from calendar events if the user is not authorized
    if requesterIsAdmin or userMakingThisRequest==event_response['Item']['user_id']:
        print("removing projects from calendar events: ")
        print(associated_events)
        removeProjectFromCalendarEvents(associated_events)


    try:
        # Now we can delete the item
        response = table.delete_item(
            Key={
                "project_name": project_name,
                "created_at": created_at
            },
            ConditionExpression=":requesterIsAdmin = :true OR user_id = :requester_id",
            ExpressionAttributeValues = {
                ":requester_id": userMakingThisRequest, 
                ":requesterIsAdmin": requesterIsAdmin,
                ":true": "true"
            }
        )
    except ClientError as e:
        print(f"error deleting project: {e}")
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
            return create_response(403, "You may only delete your own projects.")
        return create_response(403, e.response['Error']['Message'])
    
    message = json.dumps(response, indent=4, cls=DecimalEncoder)
    print(f"success deleting project; message: {message}")
    return create_response(200, message)


if __name__=="__main__":

    projects_table = "photonranch-projects"

    time = "2020-05-12T16:40:00Z" # This should be during 'cool cave' at ALI-sim
    site = "ALI-sim"
    user_id = "google-oauth2|100354044221813550027"

    event = {
        "body": json.dumps({
            "user_id": user_id,
            "site": site,
            "time": time
        })
    }

    event = {
        "body": json.dumps({
            "project_name": "m101",
            "created_at": "2020-06-24T16:53:56Z",
            "target_index": 0,
            "exposure_index": 0,
            "base_filename": "test_filename",
        })
    }
    addProjectData(event, {})

    #print(isUserScheduled(event, {}))
    #print(getUserEventsEndingAfterTime(event, {}))




