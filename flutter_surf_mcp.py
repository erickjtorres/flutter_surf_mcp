#!/usr/bin/env python3
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from app_use.app.app import App


# Initialize FastMCP server
mcp = FastMCP("flutter-control")

# Global variables to store App instance
app = None
is_connected = False

@mcp.tool()
async def connect_to_flutter_app(vm_service_uri: str) -> str:
    """Connect to a running Flutter application.

    Args:
        vm_service_uri: The WebSocket URI of the Flutter app's VM service (e.g., ws://127.0.0.1:50505/ws)
    """
    global app, is_connected

    # Close existing connection if there is one
    if app is not None:
        app.close()

    try:
        # Create a new App instance
        app = App(vm_service_uri=vm_service_uri)
        is_connected = True
        
        return f"Successfully connected to Flutter app at {vm_service_uri}"
    except Exception as e:
        is_connected = False
        return f"Error connecting to Flutter app: {str(e)}"

@mcp.tool()
async def get_app_state() -> str:
    """Get the current state of the Flutter application (widget tree).
    
    Returns a detailed representation of the current UI elements in the app.
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    try:
        # Get app state
        node_state = app.get_app_state()
        
        # Use the to_json method provided by NodeState
        formatted_state = format_widget_tree(node_state)
        
        # if result exceeds maximum length of 1000000 trim the result
        if len(formatted_state) > 1000000:
            formatted_state = formatted_state[:1000000]
        
        return formatted_state
    except Exception as e:
        return f"Error getting app state: {str(e)}"

@mcp.tool()
async def click_widget(widget_id: str) -> str:
    """Click on a widget in the Flutter app by its unique ID.

    Args:
        widget_id: The unique ID of the widget to click
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    try:
        # Convert widget_id to int for comparison
        try:
            target_unique_id = int(widget_id)
        except ValueError:
            return f"Invalid widget ID format: '{widget_id}'. ID should be an integer."

        # Get current app state to have the node_state object
        node_state = app.get_app_state()
        
        # Find widget by ID from selector_map
        target_node = node_state.selector_map.get(target_unique_id)
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if hasattr(target_node, 'text') and target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Click the widget
        success = app.click_widget_by_unique_id(node_state, int(widget_id))
        
        if success:
            return f"Successfully clicked on {widget_type} widget with text '{widget_text}' and key '{widget_key}'."
        else:
            return f"Failed to click on {widget_type} widget with text '{widget_text}' and key '{widget_key}'. The widget might not be interactive."
            
    except Exception as e:
        return f"Error clicking widget: {str(e)}"

@mcp.tool()
async def enter_text(widget_id: str, text: str) -> str:
    """Enter text into a widget in the Flutter app by its unique ID.

    Args:
        widget_id: The unique ID of the widget to enter text into
        text: The text to enter into the widget
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    try:
        # Convert widget_id to int for comparison
        try:
            target_unique_id = int(widget_id)
        except ValueError:
            return f"Invalid widget ID format: '{widget_id}'. ID should be an integer."

        # Get current app state to have the node_state object
        node_state = app.get_app_state()
        
        # Find widget by ID from selector_map
        target_node = node_state.selector_map.get(target_unique_id)
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if hasattr(target_node, 'text') and target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Enter text in the widget
        success = app.enter_text_with_unique_id(node_state, int(widget_id), text)
        
        if success:
            return f"Successfully entered text '{text}' into {widget_type} widget with previous text '{widget_text}' and key '{widget_key}'."
        else:
            return f"Failed to enter text into {widget_type} widget with text '{widget_text}' and key '{widget_key}'. The widget might not support text input."
            
    except Exception as e:
        return f"Error entering text into widget: {str(e)}"

@mcp.tool()
async def find_widgets(search_by: str = "all", search_value: str = "") -> str:
    """Find widgets in the Flutter app by key, text, or type.

    Args:
        search_by: What to search by - "key", "text", "type", or "all" (default)
        search_value: The value to search for
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    try:
        # Get current app state
        node_state = app.get_app_state()
        
        matches = []
        search_value = search_value.lower()
        
        # Search by the specified criteria
        for uid, node in node_state.selector_map.items():
            if search_by == "key" and node.key and search_value in node.key.lower():
                matches.append(node)
            elif search_by == "text" and hasattr(node, 'text') and node.text and search_value in node.text.lower():
                matches.append(node)
            elif search_by == "type" and search_value in node.widget_type.lower():
                matches.append(node)
            elif search_by == "all":
                # Search in all fields
                if (node.key and search_value in node.key.lower()) or \
                   (hasattr(node, 'text') and node.text and search_value in node.text.lower()) or \
                   (search_value in node.widget_type.lower()):
                    matches.append(node)
        
        # Format the results
        if not matches:
            return f"No widgets found matching '{search_value}' in {search_by}."
        
        result = f"Found {len(matches)} widgets matching '{search_value}' in {search_by}:\n\n"
        
        for i, node in enumerate(matches, 1):
            node_json = node.to_json()
            result += f"{i}. Type: {node.widget_type}\n"
            result += f"   ID: {node.unique_id}\n"
            result += f"   Parent ID: {node.parent.unique_id if node.parent else 'None'}\n"
            result += f"   Children IDs: {', '.join([str(child.unique_id) for child in node.child_nodes]) if node.child_nodes else 'None'}\n"
            
            if 'properties' in node_json:
                result += f"   Properties: {node_json['properties']}\n"
            
            if node.key:
                result += f"   Key: {node.key}\n"
            
            if hasattr(node, 'text') and node.text:
                result += f"   Text: {node.text}\n"
                
            result += f"   Interactive: {'Yes' if node.is_interactive else 'No'}\n"
            result += "\n"
            
        return result
            
    except Exception as e:
        return f"Error finding widgets: {str(e)}"

@mcp.tool()
async def scroll_widget_into_view(widget_id: str) -> str:
    """Scroll a widget into view in the Flutter app by its unique ID.

    Args:
        widget_id: The unique ID of the widget to scroll into view
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    try:
        # Convert widget_id to int for comparison
        try:
            target_unique_id = int(widget_id)
        except ValueError:
            return f"Invalid widget ID format: '{widget_id}'. ID should be an integer."

        # Get current app state to have the node_state object
        node_state = app.get_app_state()
        
        # Find widget by ID from selector_map
        target_node = node_state.selector_map.get(target_unique_id)
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if hasattr(target_node, 'text') and target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget into view
        success = app.scroll_into_view(node_state, target_unique_id)
        
        if success:
            return f"Successfully scrolled {widget_type} widget into view with text '{widget_text}' and key '{widget_key}'."
        else:
            return f"Failed to scroll {widget_type} widget into view with text '{widget_text}' and key '{widget_key}'. The widget might not be scrollable."
            
    except Exception as e:
        return f"Error scrolling widget into view: {str(e)}"

@mcp.tool()
async def scroll_widget_normal(widget_id: str, direction: str = "down") -> str:
    """Scroll a widget up or down in the Flutter app using standard scrolling.

    Args:
        widget_id: The unique ID of the widget to scroll
        direction: The scroll direction, either "up" or "down"
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    # Validate direction
    if direction not in ["up", "down"]:
        return "Invalid direction. Use 'up' or 'down'."
    
    try:
        # Convert widget_id to int for comparison
        try:
            target_unique_id = int(widget_id)
        except ValueError:
            return f"Invalid widget ID format: '{widget_id}'. ID should be an integer."

        # Get current app state to have the node_state object
        node_state = app.get_app_state()
        
        # Find widget by ID from selector_map
        target_node = node_state.selector_map.get(target_unique_id)
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if hasattr(target_node, 'text') and target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget
        success = app.scroll_up_or_down(node_state, target_unique_id, direction=direction)
        
        if success:
            return f"Successfully scrolled {direction} {widget_type} widget with text '{widget_text}' and key '{widget_key}'."
        else:
            return f"Failed to scroll {direction} {widget_type} widget with text '{widget_text}' and key '{widget_key}'. The widget might not be scrollable."
            
    except Exception as e:
        return f"Error scrolling widget: {str(e)}"

@mcp.tool()
async def scroll_widget(widget_id: str, direction: str = "down", dx: int = 0, dy: int = 100, duration_ms: int = 300) -> str:
    """Scroll a widget with extended parameters in the Flutter app.

    Args:
        widget_id: The unique ID of the widget to scroll
        direction: The scroll direction, either "up" or "down"
        dx: Horizontal scroll amount (positive = right, negative = left)
        dy: Vertical scroll amount (positive = down, negative = up)
        duration_ms: Duration of the scroll gesture in milliseconds
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
    
    # Validate direction
    if direction not in ["up", "down"]:
        return "Invalid direction. Use 'up' or 'down'."
    
    try:
        # Convert widget_id to int for comparison
        try:
            target_unique_id = int(widget_id)
        except ValueError:
            return f"Invalid widget ID format: '{widget_id}'. ID should be an integer."

        # Get current app state to have the node_state object
        node_state = app.get_app_state()
        
        # Find widget by ID from selector_map
        target_node = node_state.selector_map.get(target_unique_id)
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if hasattr(target_node, 'text') and target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget with extended parameters
        success = app.scroll_up_or_down_extended(
            node_state, 
            target_unique_id, 
            direction=direction, 
            dx=dx, 
            dy=dy, 
            duration_microseconds=duration_ms * 1000,  # Convert ms to microseconds
            frequency=60
        )
        
        if success:
            return f"Successfully performed extended scroll {direction} on {widget_type} widget with text '{widget_text}' and key '{widget_key}'."
        else:
            return f"Failed to perform extended scroll {direction} on {widget_type} widget with text '{widget_text}' and key '{widget_key}'. The widget might not be scrollable."
            
    except Exception as e:
        return f"Error scrolling widget with extended parameters: {str(e)}"

@mcp.tool()
async def toggle_debug_paint_feature(enable: bool = True) -> str:
    """Enable or disable the Flutter debug paint feature.

    Args:
        enable: True to enable debug paint, False to disable. Defaults to True.
    """
    global app, is_connected
    
    if not is_connected or app is None:
        return "Not connected to a Flutter app. Please connect first using connect_to_flutter_app."
        
    try:
        response = app.client.toggle_debug_paint(enable=enable)
        if response.success:
            status = "enabled" if enable else "disabled"
            return f"Debug paint feature has been {status}."
        else:
            return f"Failed to toggle debug paint: {response.message}"
    except Exception as e:
        return f"Error toggling debug paint: {str(e)}"

def format_widget_tree(node_state: Any) -> str:
    """Format the widget tree in a readable way for Claude to understand the UI structure."""
    try:
        # Use the to_json method provided by NodeState
        if hasattr(node_state, 'to_json'):
            json_data = node_state.to_json()
            
            # Create a human-readable structure with the JSON data
            result = "Flutter App UI Structure:\n\n"
            
            # Format the element tree
            result += "Element Tree:\n"
            result += format_json_node(json_data['element_tree'], 0)
            
            # Optional: Add summary info
            result += "\nUI Summary:\n"
            result += f"- Total nodes: {len(node_state.selector_map)}\n"
            result += f"- Interactive nodes: {sum(1 for node in node_state.selector_map.values() if node.is_interactive)}\n"
            
            return result
        else:
            # Fallback for cases where to_json is not available
            return f"Node state doesn't support to_json serialization. Raw data: {str(node_state)}"
    except Exception as e:
        return f"Error formatting widget tree: {str(e)}\nRaw data: {str(node_state)}"

def format_json_node(node_json, depth=0):
    """Recursively format a node JSON structure with indentation."""
    indent = "  " * depth
    result = f"{indent}ID: {node_json['id']} - Type: {node_json['widget_type']}\n"
    
    # Add text if present
    if 'text' in node_json and node_json['text']:
        result += f"{indent}  Text: {node_json['text']}\n"
    
    # Add key if present
    if 'key' in node_json and node_json['key']:
        result += f"{indent}  Key: {node_json['key']}\n"
    
    # Add interactivity info
    if 'interactive' in node_json:
        result += f"{indent}  Interactive: {'Yes' if node_json['interactive'] else 'No'}\n"
    
    # Add properties if present
    if 'properties' in node_json and node_json['properties']:
        result += f"{indent}  Properties: {str(node_json['properties'])}\n"
    
    # Add children
    if 'children' in node_json and node_json['children']:
        result += f"{indent}  Children: {len(node_json['children'])}\n"
        for child in node_json['children']:
            result += format_json_node(child, depth + 1)
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')