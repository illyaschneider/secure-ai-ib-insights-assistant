VALID_ROLES = {
    "analyst",
    "senior_analyst",
    "admin",
}
ROLE_PERMISSIONS = {
    "analyst": {
        "revenue_ranking",
        "pipeline_comparison",
        "sector_analysis",
    },
    "senior_analyst": {
        "revenue_ranking",
        "pipeline_comparison",
        "sector_analysis",
        "ai_polishing",
        "document_search",
    },
    "admin": {"*"},
}

class PermissionDeniedError(Exception):
    def __init__(self, role: str, permission: str):
        self.role = role
        self.permission = permission
        self.message = f"Role {role} does not have permission: {permission}"
        super().__init__(self.message)


def normalize_role(role: str) -> str:
    return str(role).strip().casefold()

def validate_role(role: str) -> str:
    canonical_role = normalize_role(role)

    if canonical_role not in VALID_ROLES:
        raise ValueError(f"Invalid role {role}")

    return canonical_role

def role_has_permission(role: str, permission: str) -> bool:
    canonical_role = validate_role(role)
    canonical_permission = normalize_role(permission)

    permissions = ROLE_PERMISSIONS[canonical_role]

    if "*" in permissions:
        return True
    return canonical_permission in permissions

def require_permission(role: str, permission: str) -> None:
    if not role_has_permission(role, permission):
        raise PermissionDeniedError(role, permission)


def main():
    result = require_permission("analyst", "ai_polishing")

    print(result)

if __name__ == "__main__":
    main()
