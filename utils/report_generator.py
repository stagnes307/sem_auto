import os

class ReportGenerator:
    def __init__(self, session_dir):
        self.session_dir = session_dir
        self.html_path = os.path.join(session_dir, "report.html")
    
    def generate_report(self):
        # Scan for images
        low_mag_dir = os.path.join(self.session_dir, "LowMag")
        high_mag_dir = os.path.join(self.session_dir, "HighMag")
        
        low_imgs = sorted(os.listdir(low_mag_dir)) if os.path.exists(low_mag_dir) else []
        high_imgs = sorted(os.listdir(high_mag_dir)) if os.path.exists(high_mag_dir) else []
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Smart-SEM Analysis Change Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f9; }}
                h1 {{ color: #333; }}
                .section {{ margin-bottom: 30px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .gallery {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                .card {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center; background: #fff; }}
                img {{ max-width: 300px; height: auto; display: block; margin-bottom: 5px; cursor: pointer; }}
                img:hover {{ transform: scale(1.05); transition: 0.2s; }}
            </style>
        </head>
        <body>
            <h1>Smart-SEM Analysis Report</h1>
            <p>Session Directory: {self.session_dir}</p>
            
            <div class="section">
                <h2>1. Low-Mag Mapping (Wide Scan)</h2>
                <div class="gallery">
                    {''.join([self._card("LowMag/" + img, img) for img in low_imgs])}
                </div>
            </div>
            
            <div class="section">
                <h2>2. High-Mag Particles (Targets)</h2>
                <div class="gallery">
                    {''.join([self._card("HighMag/" + img, img) for img in high_imgs])}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(self.html_path, "w", encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[Report] Generated report at {self.html_path}")
        return self.html_path

    def _card(self, rel_path, title):
        return f"""
        <div class="card">
            <a href="{rel_path}" target="_blank"><img src="{rel_path}" alt="{title}"></a>
            <span>{title}</span>
        </div>
        """
