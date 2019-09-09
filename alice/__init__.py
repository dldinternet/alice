from flask import Flask, request, jsonify, abort
import simplejson as json
from alice.main.runner import RunChecks
from alice.helper.log_utils import LOG
from alice.commons.base_jira import JiraPayloadParser
from alice.main.jira_actor import JiraActor

app = Flask(__name__)


def verify_request(payload, token):
    import hmac
    import hashlib
    import base64

    key = bytes('fHA3ogLICKad4JLU7jY9juYqZHQjBIXa608NLtFd', 'utf-8')
    # payload = bytes(payload, 'utf-8')
    digest = hmac.new(key, msg=payload, digestmod=hashlib.sha1)
    signature = digest.hexdigest()
    print("sha1=" + signature, "\n\n\n\n\n")
    if hmac.compare_digest(signature, token):
        print("hi")
    return 1/0


@app.route("/alice", methods=['POST'])
def alice():
    payload = request.get_data()
    verify_request(payload, request.headers['X-Hub-Signature'])
    payload = json.loads(payload)
    merge_correctness = RunChecks().run_checks(payload)
    return jsonify(merge_correctness)


@app.route("/", methods=['GET', 'POST'])
def home():
    return "************ Welcome to the wonderful world of Alice ***********"


# view to handle data coming from jira webhook
@app.route("/alice/jira", methods=['GET', 'POST'])
def jira_integration():
    if request.method == 'GET':
        return "************ listening from jira webhook ***********"
    if request.method == 'POST':
        payload = request.get_data()
        print("************* payload ***************", payload)
        data = json.loads(payload)
        print("************* data ***************", data)
        parsed_data = JiraPayloadParser(request, data)
        actor_obj = JiraActor(parsed_data)
        if parsed_data.webhook_event == "jira:issue_updated":
            actor_obj.get_slack_users()
            actor_obj.handle_issue_update()
        elif parsed_data.webhook_event == "jira:issue_created":
            actor_obj.get_slack_users()
            actor_obj.handle_issue_create()
        else:
            actor_obj.fetch_users()  # fetch users mentioned in jira comment which are jira user key
            actor_obj.fetch_email()  # fetch respective email of users mentioned in jira comment using jira user keys
            actor_obj.get_slack_users()  # fetch current slack user
            actor_obj.slack_jira_map()  # create jira slack map {<jira_user_key> : <slack_user_id>}
            actor_obj.send_to_slack() 
        return "******** jira post request ************"


@app.before_first_request
def setup_logging():
    if not app.debug:
        LOG.debug('************ log from setup_config *********')
