import inspect

class DocumentationManager:
    @staticmethod
    def render_docs_html(routes):
        route_cards_html = ""
        for path, methods in sorted(routes.items()):
            for method, func in methods.items():
                badge_color = "#34d399" if method == "GET" else "#60a5fa" if method == "POST" else "#f59e0b" if method == "PUT" else "#f87171"
                docstring = inspect.getdoc(func) or "No documentation provided for this endpoint."
                
                route_cards_html += f"""
                <div class="route-card" data-path="{path}" data-method="{method}">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <span class="method-badge" style="background-color: {badge_color};">{method}</span>
                        <span class="route-path">{path}</span>
                    </div>
                    <p style="color: #9ca3af; font-size: 0.9rem; line-height: 1.4; margin: 4px 0 12px 0;">{docstring}</p>
                    <div style="font-size: 0.8rem; color: #6b7280; font-family: monospace;">Handler: {func.__name__}()</div>
                </div>
                """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Custom Framework API Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 40px 20px; }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                h1 {{ font-size: 2rem; color: #fff; margin-bottom: 8px; }}
                .subtitle {{ color: #94a3b8; margin-bottom: 32px; font-size: 1.1rem; }}
                .search-bar {{ width: 100%; padding: 12px 16px; background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 1rem; margin-bottom: 24px; box-sizing: border-box; }}
                .search-bar:focus {{ outline: 2px solid #3b82f6; border-color: transparent; }}
                .route-card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; margin-bottom: 16px; transition: transform 0.2s, border-color 0.2s; }}
                .route-card:hover {{ border-color: #475569; transform: translateY(-1px); }}
                .method-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 0.8rem; width: 60px; text-align: center; font-family: monospace; }}
                .route-path {{ font-size: 1.1rem; font-weight: 600; color: #f1f5f9; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ API Interactive Dashboard</h1>
                <p class="subtitle">Auto-generated OpenAPI blueprint detailing active backend route handlers.</p>
                <input type="text" id="search" class="search-bar" placeholder="Filter routes by path or method (e.g. GET, /user)..." oninput="filterRoutes()">
                <div id="routes-list">
                    {route_cards_html}
                </div>
            </div>
            <script>
                function filterRoutes() {{
                    const query = document.getElementById('search').value.toLowerCase();
                    const cards = document.querySelectorAll('.route-card');
                    cards.forEach(card => {{
                        const path = card.getAttribute('data-path').toLowerCase();
                        const method = card.getAttribute('data-method').toLowerCase();
                        if (path.includes(query) || method.includes(query)) {{
                            card.style.display = 'block';
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """
