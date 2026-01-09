import json
import os

files = [
    "buscador_resultados/resultados_marzo_2025.json",
    "buscador_resultados/resultados_enero_2025.json",
    "buscador_resultados/resultados_enero_2025_parcial.json"
]

matches_to_find = [
    {"home": "Central Córdoba", "away": "Belgrano"},
    {"home": "Racing Club", "away": "Argentinos Juniors"},
    {"home": "Defensa y Justicia", "away": "Barracas Central"},
    {"home": "Newells", "away": "Rosario Central"},
    {"home": "Deportivo Riestra", "away": "Talleres"},
    {"home": "Lanus", "away": "Velez"}
]

found_matches = {}

for file_path in files:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for match_key, score in data.items():
                match_key_lower = match_key.lower()
                for target in matches_to_find:
                    h = target["home"].lower()
                    a = target["away"].lower()
                    
                    # Loose matching because names might vary (e.g. "Newell's" vs "Newells")
                    if h in match_key_lower and a in match_key_lower:
                        # Check order roughly (home vs away)
                        if match_key_lower.find(h) < match_key_lower.find(a):
                             found_matches[f"{target['home']} vs {target['away']}"] = score
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

print(json.dumps(found_matches, indent=2))
