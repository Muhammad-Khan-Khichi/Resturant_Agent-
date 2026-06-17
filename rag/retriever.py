def search(query: str) -> list[str]:
    """Read menu from file and return relevant sections."""
    import os
    
    menu_path = os.path.join(os.path.dirname(__file__), "..", "menu.txt")
    
    try:
        with open(menu_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [content]
    except Exception as e:
        return [f"Menu not available: {e}"]