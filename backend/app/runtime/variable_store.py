import re
from typing import Any, Dict


class VariableStore:
    """Thread-safe variable store & template expression interpolator (e.g. {{step_1.output.id}} or {{$json.email}})."""

    def __init__(self, initial_vars: Dict[str, Any] = None) -> None:
        self._store: Dict[str, Any] = dict(initial_vars or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._store)

    def interpolate(self, target: Any, scope: Dict[str, Any]) -> Any:
        """Recursively interpolates {{path.to.value}} strings in dicts, lists, or strings using scope dictionary."""
        if isinstance(target, str):
            # Match any expression inside {{ ... }}
            pattern = r"\{\{\s*([^\}]+)\s*\}\}"
            matches = re.findall(pattern, target)
            if not matches:
                return target

            # If target is exactly one template expression "{{path.to.var}}", return the raw resolved value
            if len(matches) == 1 and target.strip() == f"{{{{{matches[0]}}}}}":
                resolved = self._resolve_path(matches[0].strip(), scope)
                return resolved if resolved is not None else target

            result_str = target
            for match in matches:
                clean_match = match.strip()
                val = self._resolve_path(clean_match, scope)
                result_str = result_str.replace(f"{{{{{match}}}}}", str(val if val is not None else ""))
            return result_str

        if isinstance(target, dict):
            return {k: self.interpolate(v, scope) for k, v in target.items()}

        if isinstance(target, list):
            return [self.interpolate(item, scope) for item in target]

        return target

    def _resolve_path(self, path: str, scope: Dict[str, Any]) -> Any:
        # Strip leading dollar sign if present (e.g. $json.email -> json.email)
        clean_path = path.lstrip("$")
        # Split path into tokens handling both dot and bracket notation (e.g. step_1.messages[0].id -> ["step_1", "messages", "0", "id"])
        raw_parts = [p.strip() for p in re.split(r"[\.\[\]]", clean_path) if p and p.strip()]

        current: Any = scope
        for part in raw_parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    unwrapped = current
                    while isinstance(unwrapped, dict) and part not in unwrapped:
                        sub = unwrapped.get("output") or unwrapped.get("body") or unwrapped.get("response") or unwrapped.get("data")
                        if isinstance(sub, dict):
                            unwrapped = sub
                        else:
                            break
                    if isinstance(unwrapped, dict) and part in unwrapped:
                        current = unwrapped[part]
                    else:
                        return None
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
        return current
