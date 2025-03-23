import os
from smolagents import tool
import json
import time 
import math
import logging
from typing import List, Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderTools")

# Global variable for the Blender connection
blender_connection = None


def set_blender_connection(connection):
    """Set the global Blender connection instance"""
    global blender_connection
    blender_connection = connection


def get_blender_connection():
    """Get the global Blender connection instance"""
    global blender_connection
    if blender_connection is None:
        raise ValueError("Blender connection not initialized")
    return blender_connection

# Basic Blender Tools


@tool
def get_scene_info() -> str:
    """
    Get information about the current Blender scene.
    Returns a JSON string containing details about the scene and objects.
    """
    blender = get_blender_connection()
    result = blender.send_command("get_scene_info")
    return json.dumps(result, indent=2)


@tool
def get_object_info(name: str) -> str:
    """
    Get detailed information about a specific object in the Blender scene.
    
    Args:
        name: The name of the object to get information about
    """
    blender = get_blender_connection()
    result = blender.send_command("get_object_info", {"name": name})
    return json.dumps(result, indent=2)


@tool
def create_object(
    type: str = "CUBE",
    name: str = None,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None
) -> str:
    """
    Create a new object in the Blender scene.
    
    Args:
        type: Object type (CUBE, SPHERE, CYLINDER, PLANE, CONE, TORUS, EMPTY, CAMERA, LIGHT)
        name: Optional name for the object
        location: Optional [x, y, z] location coordinates
        rotation: Optional [x, y, z] rotation in radians
        scale: Optional [x, y, z] scale factors
    """
    blender = get_blender_connection()
    params = {"type": type}

    if name:
        params["name"] = name
    if location:
        params["location"] = location
    if rotation:
        params["rotation"] = rotation
    if scale:
        params["scale"] = scale

    result = blender.send_command("create_object", params)
    return f"Created {type} object: {result['name']}"


@tool
def modify_object(
    name: str,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None,
    visible: bool = None
) -> str:
    """
    Modify an existing object in the Blender scene.
    
    Args:
        name: Name of the object to modify
        location: Optional [x, y, z] location coordinates
        rotation: Optional [x, y, z] rotation in radians
        scale: Optional [x, y, z] scale factors
        visible: Optional boolean to set visibility
    """
    blender = get_blender_connection()
    params = {"name": name}

    if location is not None:
        params["location"] = location
    if rotation is not None:
        params["rotation"] = rotation
    if scale is not None:
        params["scale"] = scale
    if visible is not None:
        params["visible"] = visible

    result = blender.send_command("modify_object", params)
    return f"Modified object: {result['name']}"


@tool
def delete_object(name: str) -> str:
    """
    Delete an object from the Blender scene.
    
    Args:
        name: Name of the object to delete
    """
    blender = get_blender_connection()
    result = blender.send_command("delete_object", {"name": name})
    return f"Deleted object: {name}"


@tool
def set_material(
    object_name: str,
    material_name: str = None,
    color: List[float] = None
) -> str:
    """
    Set or create a material for an object.
    
    Args:
        object_name: Name of the object to apply the material to
        material_name: Optional name of the material to use or create
        color: Optional [R, G, B] color values (0.0-1.0)
    """
    blender = get_blender_connection()
    params = {"object_name": object_name}

    if material_name:
        params["material_name"] = material_name
    if color:
        params["color"] = color

    result = blender.send_command("set_material", params)
    return f"Applied material to {object_name}"


@tool
def execute_blender_code(code: str) -> str:
    """
    Execute arbitrary Python code in Blender.
    
    Args:
        code: The Python code to execute
    """
    blender = get_blender_connection()
    result = blender.send_command("execute_code", {"code": code})
    return "Code executed successfully"


# Local File Import Tool
@tool
def import_model(file_path: str, name: str = None) -> str:
    """
    Import a 3D model from a local file into the Blender scene.
    Supports GLB, FBX, OBJ, and other common 3D formats. 
    Example:
    ```py
    import_model(file_path="./car.glb", name="car")
    ```
    
    Args:
        file_path: Full path to the 3D model file (must be .glb, .fbx, .obj, or other supported format)
        name: Optional name to give the imported model in Blender. If not provided, the original filename will be used.
    """
    blender = get_blender_connection()

    # Create the parameters
    params = {"file_path": file_path}
    if name:
        params["name"] = name

    # Call the import_model function in the addon
    result = blender.send_command("import_model", params)

    # Process the result
    if "error" in result:
        return f"Error importing model: {result['error']}"

    # Success case
    main_object = result.get("main_object", {})
    main_object_name = main_object.get("name", "Unknown")
    imported_objects = result.get("imported_objects", [])
    total_objects = len(imported_objects)

    return f"Successfully imported {file_path}. Main object: '{main_object_name}'. Total objects imported: {total_objects}."


# PolyHaven Integration Tools

@tool
def get_polyhaven_status() -> str:
    """
    Check if PolyHaven integration is enabled in Blender.
    Returns a message indicating whether PolyHaven features are available.
    """
    blender = get_blender_connection()
    result = blender.get_polyhaven_status()
    enabled = result.get("enabled", False)
    message = result.get("message", "")

    return message


@tool
def get_polyhaven_categories(asset_type: str = "hdris") -> str:
    """
    Get a list of categories for a specific asset type on PolyHaven.
    
    Args:
        asset_type: The type of asset to get categories for (hdris, textures, models, all)
    """
    blender = get_blender_connection()

    # First check if PolyHaven is enabled
    ph_status = blender.get_polyhaven_status()
    if not ph_status.get("enabled", False):
        return ph_status.get("message", "PolyHaven integration is not enabled in Blender.")

    result = blender.send_command("get_polyhaven_categories", {
                                  "asset_type": asset_type})

    if "error" in result:
        return f"Error: {result['error']}"

    # Format the categories in a more readable way
    categories = result.get("categories", {})
    formatted_output = f"Categories for {asset_type}:\n\n"

    # Sort categories by count (descending)
    sorted_categories = sorted(
        categories.items(), key=lambda x: x[1], reverse=True)

    for category, count in sorted_categories:
        formatted_output += f"- {category}: {count} assets\n"

    return formatted_output


@tool
def search_polyhaven_assets(
    asset_type: str = "all",
    categories: str = None
) -> str:
    """
    Search for assets on PolyHaven with optional filtering.
    
    Args:
        asset_type: Type of assets to search for (hdris, textures, models, all)
        categories: Optional comma-separated list of categories to filter by
    """
    blender = get_blender_connection()

    # First check if PolyHaven is enabled
    ph_status = blender.get_polyhaven_status()
    if not ph_status.get("enabled", False):
        return ph_status.get("message", "PolyHaven integration is not enabled in Blender.")

    params = {"asset_type": asset_type}
    if categories:
        params["categories"] = categories

    result = blender.send_command("search_polyhaven_assets", params)

    if "error" in result:
        return f"Error: {result['error']}"

    # Format the assets in a more readable way
    assets = result.get("assets", {})
    total_count = result.get("total_count", 0)
    returned_count = result.get("returned_count", 0)

    formatted_output = f"Found {total_count} assets"
    if categories:
        formatted_output += f" in categories: {categories}"
    formatted_output += f"\nShowing {returned_count} assets:\n\n"

    # Sort assets by download count (popularity)
    sorted_assets = sorted(assets.items(), key=lambda x: x[1].get(
        "download_count", 0), reverse=True)

    for asset_id, asset_data in sorted_assets:
        formatted_output += f"- {asset_data.get('name', asset_id)} (ID: {asset_id})\n"
        formatted_output += f"  Type: {['HDRI', 'Texture', 'Model'][asset_data.get('type', 0)]}\n"
        formatted_output += f"  Categories: {', '.join(asset_data.get('categories', []))}\n"
        formatted_output += f"  Downloads: {asset_data.get('download_count', 'Unknown')}\n\n"

    return formatted_output


@tool
def download_polyhaven_asset(
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None
) -> str:
    """
    Download and import a PolyHaven asset into Blender.
    
    Args:
        asset_id: The ID of the asset to download
        asset_type: The type of asset (hdris, textures, models)
        resolution: The resolution to download (e.g., 1k, 2k, 4k)
        file_format: Optional file format (e.g., hdr, exr for HDRIs; jpg, png for textures; gltf, fbx for models)
    """
    blender = get_blender_connection()

    # First check if PolyHaven is enabled
    ph_status = blender.get_polyhaven_status()
    if not ph_status.get("enabled", False):
        return ph_status.get("message", "PolyHaven integration is not enabled in Blender.")

    params = {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "resolution": resolution
    }

    if file_format:
        params["file_format"] = file_format

    result = blender.send_command("download_polyhaven_asset", params)

    if "error" in result:
        return f"Error: {result['error']}"

    if result.get("success"):
        message = result.get(
            "message", "Asset downloaded and imported successfully")

        # Add additional information based on asset type
        if asset_type == "hdris":
            return f"{message}. The HDRI has been set as the world environment."
        elif asset_type == "textures":
            material_name = result.get("material", "")
            maps = ", ".join(result.get("maps", []))
            return f"{message}. Created material '{material_name}' with maps: {maps}."
        elif asset_type == "models":
            imported_objects = ", ".join(result.get("imported_objects", []))
            return f"{message}. Imported objects: {imported_objects}."
        else:
            return message
    else:
        return f"Failed to download asset: {result.get('message', 'Unknown error')}"


@tool
def set_texture(
    object_name: str,
    texture_id: str
) -> str:
    """
    Apply a previously downloaded PolyHaven texture to an object.
    
    Args:
        object_name: Name of the object to apply the texture to
        texture_id: ID of the PolyHaven texture to apply (must be downloaded first)
    """
    blender = get_blender_connection()

    # First check if PolyHaven is enabled
    ph_status = blender.get_polyhaven_status()
    if not ph_status.get("enabled", False):
        return ph_status.get("message", "PolyHaven integration is not enabled in Blender.")

    params = {
        "object_name": object_name,
        "texture_id": texture_id
    }

    result = blender.send_command("set_texture", params)

    if "error" in result:
        return f"Error: {result['error']}"

    if result.get("success"):
        material_name = result.get("material", "")
        maps = ", ".join(result.get("maps", []))
        return f"Successfully applied texture '{texture_id}' to {object_name} using material '{material_name}' with maps: {maps}."
    else:
        return f"Failed to apply texture: {result.get('message', 'Unknown error')}"

# Hyper3D Rodin Integration (3D model generation)


@tool
def get_hyper3d_status() -> str:
    """
    Check if Hyper3D Rodin integration is enabled in Blender.
    Returns a message indicating whether Hyper3D Rodin features are available.
    """
    blender = get_blender_connection()
    result = blender.get_hyper3d_status()
    message = result.get("message", "")

    return message


@tool
def generate_3d_model_from_text(
    text_prompt: str,
    model_name: str,
    bbox_condition: List[float] = None
) -> str:
    """
    Generate a 3D model using Hyper3D Rodin by providing a text description.
    
    Args:
        text_prompt: A description of the desired 3D model
        model_name: The name to give to the generated model
        bbox_condition: Optional [length, width, height] ratio constraint for the model
    """
    blender = get_blender_connection()

    # First check if Hyper3D is enabled
    h3d_status = blender.get_hyper3d_status()
    if not h3d_status.get("enabled", False):
        return h3d_status.get("message", "Hyper3D Rodin integration is not enabled in Blender.")

    # 1. Create the generation job
    job_params = {
        "text_prompt": text_prompt,
        "images": None,
        "bbox_condition": bbox_condition
    }

    job_result = blender.send_command("create_rodin_job", job_params)

    if "error" in job_result:
        return f"Error creating generation job: {job_result['error']}"

    # Extract necessary information to poll status
    job_id = None
    subscription_key = None
    request_id = None

    if "uuid" in job_result:
        job_id = job_result["uuid"]
        subscription_key = job_result.get("jobs", {}).get("subscription_key")
    elif "request_id" in job_result:
        request_id = job_result["request_id"]
    else:
        return f"Error: Unexpected job result format: {job_result}"

    # 2. Poll for job completion (simplified - in a real implementation, you'd want to do this asynchronously)
    max_attempts = 60  # 5 minutes with 5-second intervals
    for attempt in range(max_attempts):
        poll_params = {}
        if subscription_key:
            poll_params["subscription_key"] = subscription_key
        elif request_id:
            poll_params["request_id"] = request_id

        status_result = blender.send_command(
            "poll_rodin_job_status", poll_params)

        # Check if job is complete based on the API response format
        is_complete = False
        if "status_list" in status_result:
            # Main site API
            statuses = status_result["status_list"]
            if all(status == "Done" for status in statuses):
                is_complete = True
            elif any(status == "Failed" for status in statuses):
                return f"Error: Job failed with status: {statuses}"
        elif "status" in status_result:
            # Fal.ai API
            if status_result["status"] == "COMPLETED":
                is_complete = True
            elif status_result["status"] not in ["IN_PROGRESS", "IN_QUEUE"]:
                return f"Error: Job failed with status: {status_result['status']}"

        if is_complete:
            break

        # Wait before polling again
        time.sleep(5)

    if not is_complete:
        return "Error: Job timed out without completion"

    # 3. Import the generated asset
    import_params = {"name": model_name}
    if job_id:
        import_params["task_uuid"] = job_id
    elif request_id:
        import_params["request_id"] = request_id

    import_result = blender.send_command(
        "import_generated_asset", import_params)

    if not import_result.get("succeed", False):
        return f"Error importing generated model: {import_result.get('error', 'Unknown error')}"

    # Return success message with model info
    return f"Successfully generated and imported 3D model '{model_name}' based on the text prompt."


# Utility tool for final answers
@tool
def final_answer(answer: str) -> str:
    """
    Provide the final answer to the task.
    
    Args:
        answer: The final answer to the task
    """
    return answer
