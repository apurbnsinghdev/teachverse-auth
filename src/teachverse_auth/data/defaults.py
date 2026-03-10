# teachverse_auth/data/defaults.py
"""Default services, roles, and permissions"""

DEFAULT_SERVICES = [
    {
        "name": "auth",
        "display_name": "Authentication Service",
        "resource_types": ["user", "role", "permission", "service"],
        "actions": ["create", "read", "update", "delete", "list", "manage"]
    },
    {
        "name": "course",
        "display_name": "Course Management",
        "resource_types": ["course", "module", "lesson", "quiz", "assignment"],
        "actions": ["create", "read", "update", "delete", "list", "publish", "archive"]
    },
    {
        "name": "user",
        "display_name": "User Management",
        "resource_types": ["profile", "settings", "preferences"],
        "actions": ["create", "read", "update", "delete", "list"]
    },
    {
        "name": "organization",
        "display_name": "Organization Management",
        "resource_types": ["org", "department", "team", "member"],
        "actions": ["create", "read", "update", "delete", "list", "manage"]
    },
    {
        "name": "payment",
        "display_name": "Payment Service",
        "resource_types": ["transaction", "payout", "invoice", "refund"],
        "actions": ["create", "read", "update", "list", "process", "refund"]
    }
]