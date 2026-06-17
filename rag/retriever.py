def search(query: str) -> list[str]:
    """Read menu from file and return relevant sections."""
    import os
    
    menu_path = os.path.join(os.path.dirname(__file__), "..", "menu.txt")
    
    try:
        with open(menu_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Filter lines that contain the query (case-insensitive)
        results = [line.strip() for line in lines if query.lower() in line.lower()]
        
        return results if results else [f"No items found for '{query}'"]
    
    except Exception as e:
        return [f"Menu not available: {e}"]