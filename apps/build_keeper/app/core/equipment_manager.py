import json
import os
import uuid
import re
from typing import List, Dict, Any

from core.logger import get_logger

logger = get_logger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "equipment_sets.json")


def load_equipment_sets() -> List[Dict[str, Any]]:
    """Loads equipment sets from the JSON file."""
    if not os.path.exists(DATA_FILE):
        logger.warning(f"Data file not found at {DATA_FILE}. Returning empty list.")
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"Loaded {len(data)} equipment sets.")
            return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading equipment sets: {e}")
        return []


def save_equipment_sets(sets: List[Dict[str, Any]]) -> None:
    """Saves equipment sets to the JSON file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sets, f, ensure_ascii=False, indent=4)
    logger.info(f"Successfully saved {len(sets)} equipment sets.")


def _get_unique_name(
    base_name: str, sets: List[Dict[str, Any]], ignore_id: str = None
) -> str:
    """Generates a unique name by appending an incrementing number if the base_name exists."""
    existing_names = [s["name"] for s in sets if s.get("id") != ignore_id]

    if base_name not in existing_names:
        return base_name

    # Check if a number is already appended like 'Name 1'
    # and find the max suffix to append n + 1
    match = re.search(r"^(.*?) (\d+)$", base_name)
    if match:
        prefix = match.group(1).strip()
    else:
        prefix = base_name.strip()

    max_num = 0
    for name in existing_names:
        if name == prefix:
            max_num = max(max_num, 0)
        else:
            match = re.search(r"^" + re.escape(prefix) + r" (\d+)$", name)
            if match:
                max_num = max(max_num, int(match.group(1)))

    return f"{prefix} {max_num + 1}"


def add_equipment_set(
    name: str, equipment_flags: Dict[str, bool], custom_names: Dict[str, str]
) -> None:
    """Adds a new equipment set ensuring the name is unique."""
    sets = load_equipment_sets()
    unique_name = _get_unique_name(name, sets)

    equipment_data = {}
    for item, has_in_set in equipment_flags.items():
        equipment_data[item] = {
            "has_in_set": has_in_set,
            "acquired": False,
            "custom_name": custom_names.get(item, ""),
        }

    new_set = {
        "id": str(uuid.uuid4()),
        "name": unique_name,
        "equipment": equipment_data,
    }

    sets.append(new_set)
    save_equipment_sets(sets)
    logger.info(f"Added new equipment set: '{unique_name}' (ID: {new_set['id']})")


def update_equipment_set(
    set_id: str,
    new_name: str,
    equipment_flags: Dict[str, bool],
    custom_names: Dict[str, str],
) -> None:
    """Updates an existing equipment set and ensures unique name."""
    sets = load_equipment_sets()

    for s in sets:
        if s["id"] == set_id:
            s["name"] = _get_unique_name(new_name, sets, ignore_id=set_id)

            for item, has_in_set in equipment_flags.items():
                if item not in s["equipment"]:
                    s["equipment"][item] = {
                        "has_in_set": False,
                        "acquired": False,
                        "custom_name": "",
                    }

                s["equipment"][item]["has_in_set"] = has_in_set
                s["equipment"][item]["custom_name"] = custom_names.get(item, "")
            logger.info(f"Updated equipment set '{set_id}' to name '{s['name']}'")
            break

    save_equipment_sets(sets)


def delete_equipment_set(set_id: str) -> bool:
    """Deletes an equipment set by its ID."""
    sets = load_equipment_sets()
    initial_length = len(sets)
    sets = [s for s in sets if s["id"] != set_id]

    if len(sets) < initial_length:
        save_equipment_sets(sets)
        logger.info(f"Deleted equipment set: {set_id}")
        return True
    logger.warning(f"Attempted to delete non-existent set: {set_id}")
    return False


def clone_equipment_set(set_id: str) -> bool:
    """Clones an equipment set by its ID."""
    sets = load_equipment_sets()
    original_set = next((s for s in sets if s["id"] == set_id), None)

    if not original_set:
        return False

    cloned_set = json.loads(
        json.dumps(original_set)
    )  # Deep copy to also copy custom names safely
    cloned_set["id"] = str(uuid.uuid4())
    cloned_set["name"] = _get_unique_name(f"{cloned_set['name']} (Clone)", sets)

    for item in cloned_set["equipment"].values():
        item["acquired"] = False

    sets.append(cloned_set)
    save_equipment_sets(sets)
    logger.info(
        f"Cloned equipment set id '{set_id}' to new set '{cloned_set['name']}' (ID: {cloned_set['id']})"
    )
    return True


def update_equipment_acquisition(
    set_id: str, equipment_key: str, acquired_status: bool
) -> None:
    """Updates the 'acquired' status of a specific item in a specific set."""
    sets = load_equipment_sets()
    for s in sets:
        if s["id"] == set_id:
            if equipment_key in s["equipment"]:
                s["equipment"][equipment_key]["acquired"] = acquired_status
                logger.info(
                    f"Set '{s['name']}' (ID: {set_id}): item '{equipment_key}' acquired status updated to {acquired_status}"
                )
                break
    save_equipment_sets(sets)
