# Enhanced BlenderMCP with PolyHaven Integration

This is an adpated version of [BlenderMCP](https://github.com/ahujasid/blender-mcp) that connects AI models from Hugging Face to Blender through the Model Context Protocol (MCP) and using the [smolagents](https://github.com/huggingface/smolagents) framework. 

> **Note:** This is just a little proof of concept right now and is still a bit buggy. Simple taks did work, but more complex ones might fail.

## Prerequisites

- Blender 3.0 or newer
- Python 3.10 or newer
- `smolagents` library

## Installation

See the [BlenderMCP](https://github.com/ahujasid/blender-mcp) repository for detailed installation instructions. 

1. Clone this repository
2. Install required packages:
   ```bash
   pip install smolagents
   ```
3. Install the BlenderMCP addon in Blender
   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "Install..." and select the `addon.py` file
   - Enable the addon by checking the box next to "Interface: Blender MCP"

## Usage

### 1. Start the Blender Addon

1. In Blender, open the 3D View sidebar (press N if not visible)
2. Find the "BlenderMCP" tab
3. (Optional) Check "Use assets from Poly Haven" to enable PolyHaven integration
4. (Optional) Check "Use Hyper3D Rodin 3D model generation" to enable Hyper3D
5. Click "Start MCP Server"

### 2. Use the Agent in Python

```python
from enhanced_blender_agent import create_blender_agent, shutdown_blender_connection

# Create the agent
agent = create_blender_agent(
    model_id="google/gemma-3-27b-it",  # Or your preferred model
    include_polyhaven=True,  # Enable PolyHaven tools
    include_hyper3d=False    # Enable/disable Hyper3D tools
)

# Use the agent to create a scene
agent.run("Create a room with wooden floor and concrete walls using PolyHaven textures")

# When done, disconnect
shutdown_blender_connection()
```

## Example Notebook

See the `blender_agent_demo.ipynb` notebook for other examples of how to use the agent.

## Tools Available

- `get_scene_info()`: Get information about the current scene
- `get_object_info(name)`: Get detailed information about a specific object
- `create_object(type, name, location, rotation, scale)`: Create a new object
- `modify_object(name, location, rotation, scale, visible)`: Modify an existing object
- `delete_object(name)`: Delete an object
- `set_material(object_name, material_name, color)`: Apply a material to an object
- `import_3d_model(file_path, name)`: Import a 3D model from a local file (.glb, .fbx, .obj, etc.)
- `execute_blender_code(code)`: Execute Python code in Blender

- `get_polyhaven_status()`: Check if PolyHaven integration is enabled
- `get_polyhaven_categories(asset_type)`: Get asset categories
- `search_polyhaven_assets(asset_type, categories)`: Search for assets
- `download_polyhaven_asset(asset_id, asset_type, resolution, file_format)`: Download and import an asset
- `set_texture(object_name, texture_id)`: Apply a PolyHaven texture to an object

## Credits

- Original BlenderMCP implementation by [ahujasid](https://github.com/ahujasid/blender-mcp)
- Smolagents library for the agent framework: [https://github.com/huggingface/smolagents](https://github.com/huggingface/smolagents)