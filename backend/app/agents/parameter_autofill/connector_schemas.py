from typing import Any, Dict

CONNECTOR_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Google Sheets": {
        "sheets.spreadsheets.values.get": {
            "value_render_option": "FORMATTED_VALUE",
        }
    },
    "Loop": {
        "loop.process": {
            "collection": "{{$node.Google_Sheets.values}}",
            "item_alias": "item",
        }
    },
    "Gmail": {
        "gmail.messages.send": {}
    },
    "Slack": {
        "slack.chat.postMessage": {}
    },
    "Google Drive": {
        "drive.files.upload": {}
    },
    "GitHub": {
        "github.pulls.list": {
            "state": "open",
        }
    },
}
