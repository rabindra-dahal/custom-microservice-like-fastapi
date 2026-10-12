class DocumentationManager:
    """
    Dynamically generates an interactive HTML documentation webpage 
    by scanning the application's active routing map.
    """
    @staticmethod
    def render_docs_html(routes_snapshot: dict) -> str:
        """
        Generates a clean HTML/CSS dashboard layout displaying paths, 
        methods, and docstring instructions for every registered endpoint.
        """
        rows_html = ""
        for path, methods in routes_snapshot.items():
            for method, func in methods.items():
                docstring = func.__doc__ or "No description provided for this endpoint."
                cleaned_doc = " ".join(docstring.split())
                
                # Append formatted HTML table structure string segment chunks
                rows_html += f"""
                <tr style='border-bottom: 1px solid #e2e8f0;'>
                    <td style='padding: 12px; font-weight: bold; color: #2b6cb0;'>{method}</td>
                    <td style='padding: 12px; font-family: monospace; color: #2d3748;'>{path}</td>
                    <td style='padding: 12px; color: #4a5568;'>{cleaned_doc}</td>
                </tr>
                """
                
        return f"""
        <html>
            <head>
                <title>Framework Interactive OpenAPI Documentation</title>
            </head>
            <body style='font-family: system-ui, sans-serif; margin: 0; padding: 40px; background: #f7fafc;'>
                <div style='max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'>
                    <h1 style='color: #1a202c; margin-top:0;'>Application Documentation Dashboard</h1>
                    <p style='color: #718096; margin-bottom: 30px;'>Automatically generated breakdown mapping active routing points.</p>
                    <table style='width: 100%; border-collapse: collapse; text-align: left;'>
                        <thead>
                            <tr style='background: #edf2f7; color: #4a5568;'>
                                <th style='padding: 12px;'>Method</th>
                                <th style='padding: 12px;'>Path Endpoint Pattern</th>
                                <th style='padding: 12px;'>Description Documentation</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """
