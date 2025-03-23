from smolagents import CodeAgent, HfApiModel
import yaml
import json
import time
import os
import logging
from typing import List, Dict, Any, Optional, Union

# Import our modules
from blender_connection import BlenderConnection
import blender_tools as tools

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderAgent")


def create_blender_agent(
    model_id: str = None,
    host: str = 'localhost',
    port: int = 9876,
    prompt_file: str = None,
    api_token: str = None,
    include_polyhaven: bool = True,
    include_hyper3d: bool = False,
    additional_imports: List[str] = None,
    temperature: float = 0.7
) -> CodeAgent:
    """
    Create a CodeAgent that can interact with Blender.
    
    Args:
        model_id: The model ID to use for the agent (defaults to google/gemma-3-27b-it if None)
        host: Blender addon host address
        port: Blender addon port
        prompt_file: Path to a YAML file containing custom prompt templates
        api_token: Hugging Face API token for accessing models
        include_polyhaven: Whether to include PolyHaven tools
        include_hyper3d: Whether to include Hyper3D Rodin tools
        additional_imports: Additional modules to authorize for import in code execution
        temperature: Temperature for model generation (higher = more creative)
    
    Returns:
        A CodeAgent instance configured to work with Blender
    """
    # Initialize the Blender connection
    blender = BlenderConnection(host=host, port=port)

    # Set it globally
    tools.set_blender_connection(blender)

    # Connect to Blender
    if not blender.connect():
        logger.warning(
            "Could not connect to Blender. Make sure the Blender addon is running.")

    # Set up the basic tools
    available_tools = [
        tools.get_scene_info,
        tools.get_object_info,
        tools.create_object,
        tools.modify_object,
        tools.delete_object,
        tools.set_material,
        tools.import_model,  
        tools.execute_blender_code,
        tools.final_answer
    ]

    # Add PolyHaven tools if enabled
    if include_polyhaven:
        # Check if PolyHaven is enabled in Blender
        ph_status = blender.get_polyhaven_status()

        # Always include the status tool
        available_tools.append(tools.get_polyhaven_status)

        if ph_status.get("enabled", False):
            logger.info(
                "PolyHaven integration is enabled in Blender, adding PolyHaven tools")
            available_tools.extend([
                tools.get_polyhaven_categories,
                tools.search_polyhaven_assets,
                tools.download_polyhaven_asset,
                tools.set_texture
            ])
        else:
            logger.warning(
                f"PolyHaven integration is disabled in Blender: {ph_status.get('message', '')}")

    # Add Hyper3D Rodin tools if enabled
    if include_hyper3d:
        # Check if Hyper3D is enabled in Blender
        h3d_status = blender.get_hyper3d_status()

        # Always include the status tool
        available_tools.append(tools.get_hyper3d_status)

        if h3d_status.get("enabled", False):
            logger.info(
                "Hyper3D Rodin integration is enabled in Blender, adding Hyper3D tools")
            available_tools.append(tools.generate_3d_model_from_text)
        else:
            logger.warning(
                f"Hyper3D Rodin integration is disabled in Blender: {h3d_status.get('message', '')}")

    # Set default model if none provided
    if not model_id:
        model_id = 'google/gemma-3-27b-it'

    # Create the model
    model = HfApiModel(
        max_tokens=128000,
        temperature=temperature,
        model_id=model_id,
        token=api_token,
        custom_role_conversions=None,
    )

    # Load custom prompt templates if provided
    prompt_templates = None
    if prompt_file:
        try:
            with open(prompt_file, 'r') as stream:
                prompt_templates = yaml.safe_load(stream)
            logger.info(f"Loaded custom prompts from {prompt_file}")
        except Exception as e:
            logger.error(f"Error loading prompts from {prompt_file}: {str(e)}")

    # Default authorized imports
    authorized_imports = ['json', 'math', 'time', 'random', 'datetime']

    # Add additional authorized imports if provided
    if additional_imports:
        authorized_imports.extend(additional_imports)

    # Create the agent
    agent = CodeAgent(
        tools=available_tools,
        model=model,
        add_base_tools=True,  # Include search, etc.
        additional_authorized_imports=authorized_imports,
        prompt_templates=prompt_templates  # Add custom prompts if provided
    )

    # If no custom prompt_templates were provided, add our Blender-specific guidance
    if not prompt_templates:
        blender_guidance = """
        You are a Blender assistant that can help users create and manipulate 3D scenes in Blender.
        
        Here's a strategy for creating 3D content in Blender:
        
        1. First use get_scene_info() to understand the current state of the scene.
        
        2. For creating and manipulating objects:
           - Use create_object() for basic primitives (CUBE, SPHERE, CYLINDER, etc.)
           - Use set_material() for basic colors and materials
           - Use modify_object() to adjust position, rotation, scale
           - Use delete_object() to remove unwanted objects
           - Use get_object_info() to get detailed information about specific objects
        
        3. For importing custom 3D models from the user's computer:
           - Use import_3d_model(file_path) to import GLB, FBX, OBJ, and other 3D file formats
           - The file_path should be the full local path to the 3D model file
           - You can optionally provide a name for the imported model
        
        4. For more realistic assets, you can use PolyHaven if it's enabled:
           - First check if PolyHaven is enabled using get_polyhaven_status()
           - Search for assets with search_polyhaven_assets()
           - Download assets with download_polyhaven_asset()
           - Apply textures to objects with set_texture()
        
        5. For AI-generated 3D models, you can use Hyper3D Rodin if it's enabled:
           - First check if Hyper3D is enabled using get_hyper3d_status()
           - Generate models with generate_3d_model_from_text()
        
        Always verify your actions after making changes to ensure the scene is as expected.
        
        When you're done with your task, use final_answer() to provide your conclusion.
        """
        agent.system_prompt += "\n\n" + blender_guidance

    return agent


def shutdown_blender_connection():
    """Disconnect from Blender"""
    try:
        # Get the globally set connection
        blender = tools.get_blender_connection()
        blender.disconnect()
        logger.info("Disconnected from Blender")
    except Exception as e:
        logger.error(f"Error disconnecting from Blender: {str(e)}")
