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
        all_nodes = app.get_app_state()
        
        # Convert to a more readable format
        formatted_nodes = format_widget_tree(all_nodes)
        
        # if greater than result exceeds maximum length of 1000000 trim the result
        if len(formatted_nodes) > 1000000:
            formatted_nodes = formatted_nodes[:1000000]
        
        return formatted_nodes
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

        # Get current app state to have the all_nodes object
        all_nodes = app.get_app_state()
        
        # Find widget by ID for better feedback
        target_node = None
        for node in all_nodes:
            if node.unique_id == target_unique_id:
                target_node = node
                break
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Click the widget
        success = app.click_widget_by_unique_id(all_nodes, int(widget_id))
        
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

        # Get current app state to have the all_nodes object
        all_nodes = app.get_app_state()
        
        # Find widget by ID for better feedback
        target_node = None
        for node in all_nodes:
            if node.unique_id == target_unique_id:
                target_node = node
                break
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Enter text in the widget
        success = app.enter_text_with_unique_id(all_nodes, int(widget_id), text)
        
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
        all_nodes = app.get_app_state()
        
        matches = []
        search_value = search_value.lower()
        
        # Search by the specified criteria
        for node in all_nodes:
            if search_by == "key" and node.key and search_value in node.key.lower():
                matches.append(node)
            elif search_by == "text" and node.text and search_value in node.text.lower():
                matches.append(node)
            elif search_by == "type" and search_value in node.widget_type.lower():
                matches.append(node)
            elif search_by == "all":
                # Search in all fields
                if (node.key and search_value in node.key.lower()) or \
                   (node.text and search_value in node.text.lower()) or \
                   (search_value in node.widget_type.lower()):
                    matches.append(node)
        
        # Format the results
        if not matches:
            return f"No widgets found matching '{search_value}' in {search_by}."
        
        result = f"Found {len(matches)} widgets matching '{search_value}' in {search_by}:\n\n"
        
        for i, node in enumerate(matches, 1):
            result += f"{i}. Type: {node.widget_type}\n"
            result += f"   ID: {node.unique_id}\n"
            result += f"   Parent ID: {node.parent_node.unique_id if node.parent_node else 'None'}\n"
            result += f"   Children IDs: {', '.join([str(child.unique_id) for child in node.child_nodes]) if node.child_nodes else 'None'}\n"
            result += f"   Properties: {node.properties}\n"
            
            if node.key:
                result += f"   Key: {node.key}\n"
            
            if node.text:
                result += f"   Text: {node.text}\n"
                
            result += f"   Interactive: {'Yes' if node.is_interactive else 'Yes'}\n"
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

        # Get current app state to have the all_nodes object
        all_nodes = app.get_app_state()
        
        # Find widget by ID for better feedback
        target_node = None
        for node in all_nodes:
            if node.unique_id == target_unique_id:
                target_node = node
                break
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget into view
        success = app.scroll_into_view(all_nodes, target_unique_id)
        
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

        # Get current app state to have the all_nodes object
        all_nodes = app.get_app_state()
        
        # Find widget by ID for better feedback
        target_node = None
        for node in all_nodes:
            if node.unique_id == target_unique_id:
                target_node = node
                break
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget
        success = app.scroll_up_or_down(all_nodes, target_unique_id, direction=direction)
        
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

        # Get current app state to have the all_nodes object
        all_nodes = app.get_app_state()
        
        # Find widget by ID for better feedback
        target_node = None
        for node in all_nodes:
            if node.unique_id == target_unique_id:
                target_node = node
                break
        
        if not target_node:
            return f"Widget with ID '{widget_id}' not found. Use get_app_state to see available widgets."
        
        # Get info for better feedback
        widget_type = target_node.widget_type
        widget_text = target_node.text if target_node.text else None
        widget_key = target_node.key if target_node.key else None
        
        # Scroll the widget with extended parameters
        success = app.scroll_up_or_down_extended(
            all_nodes, 
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

def format_widget_tree(nodes: Any) -> str:
    """Format the widget tree in a readable way for Claude to understand the UI structure."""
    result = "Flutter App UI Structure:\n\n"
    
    def process_node(node, depth=0):
        nonlocal result
        
        # Extract widget properties from AppNode object
        widget_id = node.unique_id
        widget_type = node.widget_type
        widget_text = node.text if node.text is not None else ""
        
        # Add this widget to the result
        result += f"id: {widget_id}"
        result += f"type: {widget_type}"
        
        if widget_text:
            result += f"text: {widget_text}"
            
        
        # Add other important properties
        if node.is_interactive:
            result += f"canClick: Yes"
        
        
        # Process children
        if node.child_nodes:
            for child in node.child_nodes:
                process_node(child, depth + 1)
    
    # Start processing from the root nodes
    if hasattr(nodes, 'unique_id'):  # Single node
        process_node(nodes)
    elif isinstance(nodes, list) and nodes:
        for node in nodes:
            if hasattr(node, 'unique_id'):  # Ensure it's a AppNode
                process_node(node)
    else:
        result += "Unable to parse widget tree structure\n"
        result += f"Raw data: {str(nodes)}\n"
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')