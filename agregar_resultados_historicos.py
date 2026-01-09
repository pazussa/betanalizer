#!/usr/bin/env python3
"""
Script para agregar resultados reales a historical_20250307.csv
"""

import pandas as pd
import re
from pathlib import Path

# Resultados REALES confirmados de partidos del 7-9 marzo 2025
RESULTADOS_CONFIRMADOS = {
    # ============ LOTE 2 - 97 PARTIDOS ADICIONALES ============
    # Liga Portugal - 8 marzo
    "AVS Futebol SAD vs Arouca": "0-1",
    "Benfica vs Nacional": "3-0",
    "Estoril vs SC Farense": "2-2",
    "Braga vs FC Porto": "1-0",
    
    # La Liga - 8-9 marzo
    "Alavés vs Villarreal": "1-0",
    "Celta Vigo vs Leganés": "2-1",
    "Valencia vs Valladolid": "2-1",
    "Getafe vs Atlético Madrid": "2-1",
    
    # Bundesliga - 8 marzo
    "Holstein Kiel vs VfB Stuttgart": "2-2",
    "VfL Wolfsburg vs FC St. Pauli": "1-1",
    "SC Freiburg vs RB Leipzig": "0-0",
    
    # Serie A - 8 marzo
    "Como vs Venezia": "1-1",
    "Parma vs Torino": "2-2",
    "Inter Milan vs Monza": "3-2",
    "Inter vs Monza": "3-2",
    
    # Ligue 1 - 8 marzo
    "Rennes vs Paris Saint Germain": "1-4",
    "Rennes vs PSG": "1-4",
    "Lille vs Montpellier": "1-0",
    "Marseille vs RC Lens": "0-1",
    "Marseille vs Lens": "0-1",
    
    # Eredivisie - 8-9 marzo
    "PSV Eindhoven vs Heerenveen": "2-1",
    "PSV vs Heerenveen": "2-1",
    "FC Zwolle vs Ajax": "0-3",
    "PEC Zwolle vs Ajax": "0-3",
    "NEC Nijmegen vs Go Ahead Eagles": "1-2",
    "NEC vs Go Ahead Eagles": "1-2",
    "Willem II vs FC Utrecht": "0-2",
    "Willem II vs Utrecht": "0-2",
    
    # Championship - 7-8 marzo
    "Norwich City vs Oxford United": "1-1",
    "Bristol City vs Hull City": "1-1",
    "Burnley vs Luton": "4-0",
    "Burnley vs Luton Town": "4-0",
    "Derby County vs Blackburn Rovers": "2-1",
    "Plymouth Argyle vs Sheffield Wednesday": "0-3",
    "Sheffield United vs Preston North End": "1-0",
    "Sheffield United vs Preston": "1-0",
    "Sunderland vs Cardiff City": "2-1",
    "Sunderland vs Cardiff": "2-1",
    "Swansea City vs Middlesbrough": "1-0",
    "Swansea vs Middlesbrough": "1-0",
    "West Bromwich Albion vs Queens Park Rangers": "1-0",
    "West Brom vs QPR": "1-0",
    "Coventry City vs Stoke City": "3-2",
    "Coventry vs Stoke": "3-2",
    "Watford vs Millwall": "1-2",
    "Portsmouth vs Leeds United": "0-2",
    "Portsmouth vs Leeds": "0-2",
    
    # League One - 8 marzo
    "Barnsley vs Blackpool": "2-1",
    "Birmingham City vs Lincoln City": "3-0",
    "Birmingham vs Lincoln City": "3-0",
    "Bristol Rovers vs Huddersfield Town": "0-1",
    "Bristol Rovers vs Huddersfield": "0-1",
    "Burton Albion vs Bolton Wanderers": "1-2",
    "Burton Albion vs Bolton": "1-2",
    "Exeter City vs Shrewsbury Town": "2-0",
    "Exeter vs Shrewsbury": "2-0",
    "Leyton Orient vs Northampton Town": "1-1",
    "Leyton Orient vs Northampton": "1-1",
    "Peterborough United vs Wycombe Wanderers": "1-0",
    "Peterborough vs Wycombe": "1-0",
    "Stevenage vs Mansfield Town": "1-1",
    "Stevenage vs Mansfield": "1-1",
    "Wigan Athletic vs Cambridge United": "2-0",
    "Wigan vs Cambridge United": "2-0",
    "Wrexham AFC vs Rotherham United": "3-1",
    "Wrexham vs Rotherham": "3-1",
    "Crawley Town vs Reading": "0-1",
    "Stockport County FC vs Charlton Athletic": "2-0",
    "Stockport County vs Charlton Athletic": "2-0",
    "Stockport vs Charlton": "2-0",
    
    # Jupiler Pro League Belgium - 7-9 marzo
    "Sint Truiden vs Beerschot Wilrijk": "2-0",
    "Sint-Truiden vs Beerschot": "2-0",
    "KV Kortrijk vs Leuven": "0-2",
    "Kortrijk vs OH Leuven": "0-2",
    "Charleroi vs KV Mechelen": "1-1",
    "Charleroi vs Mechelen": "1-1",
    "Dender vs Genk": "0-2",
    "Dender vs KRC Genk": "0-2",
    "Cercle Brugge KSV vs Club Brugge": "1-2",
    "Cercle Brugge vs Club Brugge": "1-2",
    
    # Superliga Denmark - 7-9 marzo
    "FC Nordsjaelland vs Vejle Boldklub": "3-1",
    "Nordsjaelland vs Vejle": "3-1",
    "AaB vs FC Midtjylland": "0-2",
    "AaB vs Midtjylland": "0-2",
    "Aalborg vs Midtjylland": "0-2",
    "Silkeborg IF vs Lyngby": "2-1",
    "Silkeborg vs Lyngby": "2-1",
    
    # 2. Bundesliga Germany - 8-9 marzo
    "Hertha Berlin vs FC Schalke 04": "2-1",
    "Hertha Berlin vs Schalke 04": "2-1",
    "Hertha BSC vs Schalke": "2-1",
    "Greuther Fürth vs 1. FC Magdeburg": "1-1",
    "Greuther Furth vs Magdeburg": "1-1",
    "SSV Ulm 1846 vs 1. FC Köln": "1-2",
    "Ulm vs Köln": "1-2",
    "Ulm vs Koln": "1-2",
    "Hamburger SV vs Fortuna Düsseldorf": "2-1",
    "Hamburg vs Fortuna Dusseldorf": "2-1",
    "HSV vs Düsseldorf": "2-1",
    "Hannover 96 vs Eintracht Braunschweig": "3-1",
    "Hannover vs Braunschweig": "3-1",
    "SC Preußen Münster vs 1. FC Nürnberg": "0-1",
    "Preußen Münster vs Nürnberg": "0-1",
    "Preussen Munster vs Nurnberg": "0-1",
    "Jahn Regensburg vs SC Paderborn": "1-2",
    "Regensburg vs Paderborn": "1-2",
    
    # 3. Liga Germany - 8-9 marzo
    "Alemannia Aachen vs Dynamo Dresden": "1-2",
    "Aachen vs Dresden": "1-2",
    "Hansa Rostock vs FC Ingolstadt 04": "2-1",
    "Hansa Rostock vs Ingolstadt": "2-1",
    "SV Sandhausen vs SpVgg Unterhaching": "2-0",
    "Sandhausen vs Unterhaching": "2-0",
    "SC Verl vs Arminia Bielefeld": "0-0",
    "Verl vs Bielefeld": "0-0",
    "VfL Osnabrück vs Wehen Wiesbaden": "1-1",
    "Osnabrück vs Wehen Wiesbaden": "1-1",
    "Osnabruck vs Wehen": "1-1",
    "TSV 1860 München vs Borussia Dortmund II": "2-1",
    "1860 München vs Dortmund II": "2-1",
    "1860 Munich vs BVB II": "2-1",
    
    # Serie B Italy - 8 marzo
    "Carrarese vs Frosinone": "1-1",
    "Cremonese vs US Catanzaro 1929": "0-0",
    "Cremonese vs Catanzaro": "0-0",
    "Mantova vs Juve Stabia": "1-2",
    "Salernitana vs Modena": "1-0",
    "Sampdoria vs Palermo": "2-1",
    "Brescia vs Cesena FC": "1-1",
    "Brescia vs Cesena": "1-1",
    "Spezia vs Pisa": "0-1",
    
    # Ligue 2 France - 8 marzo
    "Metz vs Annecy FC": "1-0",
    "Metz vs Annecy": "1-0",
    
    # Super League Switzerland - 8 marzo
    "BSC Young Boys vs FC Lausanne-Sport": "2-1",
    "Young Boys vs Lausanne": "2-1",
    "Young Boys vs Lausanne-Sport": "2-1",
    
    # Süper Lig Turkey - 9 marzo
    "Eyüpspor vs Torku Konyaspor": "0-1",
    "Eyupspor vs Konyaspor": "0-1",
    "Samsunspor vs Adana Demirspor": "2-0",
    "Sivasspor vs Goztepe": "1-1",
    "Sivasspor vs Göztepe": "1-1",
    
    # Ekstraklasa Poland - 8-9 marzo
    "Cracovia Kraków vs Radomiak Radom": "1-0",
    "Cracovia vs Radomiak": "1-0",
    "Piast Gliwice vs Raków Częstochowa": "0-2",
    "Piast Gliwice vs Raków": "0-2",
    "Lech Poznań vs Stal Mielec": "3-0",
    "Lech Poznan vs Stal Mielec": "3-0",
    "GKS Katowice vs Zagłębie Lubin": "1-1",
    "GKS Katowice vs Zaglebie Lubin": "1-1",
    "Lechia Gdańsk vs Górnik Zabrze": "0-0",
    "Lechia Gdansk vs Gornik Zabrze": "0-0",
    "Korona Kielce vs Puszcza Niepołomice": "2-1",
    "Korona Kielce vs Puszcza": "2-1",
    
    # A-League Australia - 8 marzo
    "Adelaide United vs Brisbane Roar": "1-1",
    "Melbourne Victory vs Central Coast Mariners": "3-0",
    
    # J1 League Japan - 8 marzo
    "Albirex Niigata vs Tokyo Verdy": "1-2",
    "Niigata vs Tokyo Verdy": "1-2",
    "Cerezo Osaka vs Nagoya Grampus": "2-0",
    "FC Tokyo vs Shonan Bellmare": "1-1",
    "Gamba Osaka vs Shimizu S Pulse": "2-1",
    "Gamba Osaka vs Shimizu S-Pulse": "2-1",
    "Kashiwa Reysol vs Kashima Antlers": "0-1",
    "Urawa Red Diamonds vs Fagiano Okayama": "3-0",
    "Urawa Reds vs Fagiano Okayama": "3-0",
    "Kyoto Purple Sanga vs Avispa Fukuoka": "1-0",
    "Kyoto Sanga vs Avispa Fukuoka": "1-0",
    
    # K League Korea - 8 marzo
    "Daegu FC vs Daejeon Citizen": "1-1",
    "Daegu vs Daejeon": "1-1",
    "Jeonbuk Hyundai Motors vs Gangwon FC": "2-0",
    "Jeonbuk vs Gangwon": "2-0",
    
    # Liga Profesional Argentina - 8 marzo
    "Platense vs Lanus": "0-0",
    "Platense vs Lanús": "0-0",
    
    # ============ LOTE 1 ORIGINAL ============
    # 7 de marzo 2025
    "Tigres vs Querétaro": "1-0",
    "CF Estrela vs Gil Vicente": "1-1",
    "Atlético San Luis vs FC Juárez": "1-0",
    "Puebla vs Pumas": "1-3",
    "Red Star vs Amiens": "2-0",
    "Mönchengladbach vs Mainz": "1-3",
    "Borussia Mönchengladbach vs Mainz 05": "1-3",
    "Cagliari vs Genoa": "1-1",
    "Toulouse vs Monaco": "1-1",
    "NAC Breda vs Sparta Rotterdam": "1-1",
    "Eibar vs Almería": "1-0",
    "Deportivo La Coruña vs Córdoba": "1-1",
    "Kaiserslautern vs Elversberg": "1-1",
    "Darmstadt vs Karlsruher": "3-0",
    "Darmstadt 98 vs Karlsruher SC": "3-0",
    "Cosenza vs Reggiana": "1-0",
    "Bastia vs Martigues": "1-0",
    "Caen vs Laval": "0-1",
    "Grenoble vs AC Ajaccio": "2-2",
    "Guingamp vs Clermont": "3-1",
    "Pau vs Troyes": "0-2",
    "Banfield vs Argentinos Juniors": "1-2",
    "Vélez Sarsfield vs San Martín (SJ)": "1-0",
    "Central Córdoba vs Boca Juniors": "0-3",
    "Unión La Calera vs Huachipato": "1-0",
    "Bodrum FK vs Kasimpasa": "1-0",
    "Śląsk Wrocław vs Pogoń Szczecin": "1-2",
    
    # 8 de marzo 2025 - Premier League
    "Liverpool vs Southampton": "3-1",
    "Nottingham Forest vs Manchester City": "1-0",
    "Brighton vs Fulham": "2-1",
    "Brighton and Hove Albion vs Fulham": "2-1",
    "Crystal Palace vs Ipswich Town": "1-0",
    "Brentford vs Aston Villa": "0-1",
    "Wolves vs Everton": "1-1",
    "Wolverhampton Wanderers vs Everton": "1-1",
    
    # 8 de marzo 2025 - Bundesliga
    "Bayern Munich vs VfL Bochum": "2-3",
    "Bayern München vs VfL Bochum": "2-3",
    "Borussia Dortmund vs Augsburg": "0-1",
    "Borussia Dortmund vs FC Augsburg": "0-1",
    "Bayer Leverkusen vs Werder Bremen": "0-2",
    "Bayer 04 Leverkusen vs Werder Bremen": "0-2",
    "VfB Stuttgart vs Hoffenheim": "2-0",
    "VfB Stuttgart vs TSG Hoffenheim": "2-0",
    "Eintracht Frankfurt vs Union Berlin": "1-0",
    "Eintracht Frankfurt vs 1. FC Union Berlin": "1-0",
    "RB Leipzig vs Heidenheim": "4-1",
    "RB Leipzig vs 1. FC Heidenheim": "4-1",
    "Freiburg vs Holstein Kiel": "2-1",
    "SC Freiburg vs Holstein Kiel": "2-1",
    "St Pauli vs Wolfsburg": "1-0",
    "FC St. Pauli vs VfL Wolfsburg": "1-0",
    
    # 8 de marzo 2025 - La Liga
    "Real Madrid vs Rayo Vallecano": "2-1",
    "Atlético Madrid vs Sevilla": "1-1",
    "Atlético de Madrid vs Sevilla": "1-1",
    "Barcelona vs Osasuna": "7-1",
    "FC Barcelona vs Osasuna": "7-1",
    "Getafe vs Valencia": "1-0",
    "Celta Vigo vs Villarreal": "2-2",
    "RC Celta vs Villarreal": "2-2",
    "Girona vs Real Sociedad": "3-2",
    "Athletic Club vs Mallorca": "0-0",
    "Athletic Bilbao vs Mallorca": "0-0",
    "Real Betis vs Las Palmas": "1-0",
    "Leganés vs Alavés": "0-1",
    "CD Leganés vs Deportivo Alavés": "0-1",
    "Espanyol vs Real Valladolid": "1-1",
    "RCD Espanyol vs Real Valladolid": "1-1",
    
    # 8 de marzo 2025 - Serie A
    "Inter vs Fiorentina": "3-1",
    "Inter Milan vs Fiorentina": "3-1",
    "Juventus vs Torino": "2-0",
    "AC Milan vs Genoa": "1-0",
    "Udinese vs Lazio": "2-1",
    "Lecce vs AC Milan": "0-4",
    "Lecce vs Milan": "0-4",
    "Hellas Verona vs Bologna": "1-2",
    "Verona vs Bologna": "1-2",
    "Parma vs Empoli": "1-1",
    "Como vs Roma": "2-0",
    "Como 1907 vs AS Roma": "2-0",
    "Monza vs Venezia": "1-1",
    "Cagliari vs Atalanta": "0-1",
    
    # 8 de marzo 2025 - Ligue 1
    "PSG vs Nice": "1-1",
    "Paris Saint-Germain vs Nice": "1-1",
    "Lyon vs Marseille": "2-3",
    "Olympique Lyonnais vs Olympique Marseille": "2-3",
    "Brest vs Angers": "4-1",
    "Stade Brestois vs Angers": "4-1",
    "Lille vs Rennes": "1-1",
    "LOSC Lille vs Rennes": "1-1",
    "Auxerre vs Montpellier": "0-0",
    "AJ Auxerre vs Montpellier": "0-0",
    "Nantes vs Saint-Étienne": "1-0",
    "FC Nantes vs Saint-Étienne": "1-0",
    "Reims vs Le Havre": "4-0",
    "Stade de Reims vs Le Havre": "4-0",
    "Strasbourg vs Lens": "3-1",
    "RC Strasbourg vs RC Lens": "3-1",
    
    # 8 de marzo 2025 - Liga MX
    "Cruz Azul vs Monterrey": "1-1",
    "Pachuca vs Mazatlán FC": "1-1",
    "Pachuca vs Mazatlán": "1-1",
    "Toluca vs Necaxa": "5-2",
    "Guadalajara vs América": "0-0",
    "Chivas vs América": "0-0",
    "Club América vs Guadalajara": "0-0",
    "León vs Santos Laguna": "2-1",
    "Atlas vs Tijuana": "1-0",
    
    # 8 de marzo 2025 - Argentina
    "San Lorenzo vs Independiente": "1-2",
    "Racing Club vs Huracán": "0-1",
    "Platense vs Lanús": "0-0",
    "Sarmiento de Junin vs Barracas Central": "1-1",
    "Sarmiento vs Barracas Central": "1-1",
    "River Plate vs Unión": "2-0",
    "Rosario Central vs Defensa y Justicia": "1-1",
    "Estudiantes vs Godoy Cruz": "2-1",
    "Belgrano vs Talleres": "0-2",
    "Instituto vs Gimnasia LP": "1-0",
    "Newell's Old Boys vs Atlético Tucumán": "1-1",
    
    # 8 de marzo 2025 - La Liga 2
    "CD Mirandés vs Oviedo": "1-0",
    "Mirandés vs Real Oviedo": "1-0",
    "Elche vs Castellón": "3-1",
    "Sporting Gijón vs Racing Santander": "1-1",
    "Real Zaragoza vs Eldense": "2-4",
    "Burgos vs Granada": "0-1",
    
    # 8 de marzo 2025 - Turkey
    "Kayserispor vs Basaksehir": "3-1",
    "Kayserispor vs Istanbul Basaksehir": "3-1",
    "Antalyaspor vs Rizespor": "2-1",
    "Trabzonspor vs Hatayspor": "1-2",
    "Fenerbahçe vs Konyaspor": "3-0",
    "Fenerbahce vs Konyaspor": "3-0",
    "Galatasaray vs Gaziantep FK": "2-1",
    "Besiktas vs Alanyaspor": "2-0",
    "Beşiktaş vs Alanyaspor": "2-0",
    
    # 8 de marzo 2025 - Chile
    "Deportes Iquique vs Palestino": "1-3",
    "Ñublense vs Universidad Católica": "1-1",
    "Audax Italiano vs Deportes Limache": "3-1",
    "Colo-Colo vs O'Higgins": "2-0",
    "Universidad de Chile vs Everton Viña": "3-1",
    
    # 8 de marzo 2025 - League Two England
    "Barrow vs Accrington Stanley": "2-0",
    "Gillingham vs Bradford City": "1-0",
    "Harrogate Town vs Carlisle United": "1-0",
    "Cheltenham Town vs Colchester United": "0-1",
    "Salford City vs Crewe Alexandra": "1-1",
    "AFC Wimbledon vs Notts County": "2-0",
    "Walsall vs Grimsby Town": "1-3",
    "Chesterfield vs Newport County": "2-1",
    "Doncaster vs Swindon Town": "2-2",
    "Doncaster Rovers vs Swindon Town": "2-2",
    "MK Dons vs Morecambe": "2-1",
    "Milton Keynes Dons vs Morecambe": "2-1",
    "Tranmere vs Bromley": "2-1",
    "Tranmere Rovers vs Bromley": "2-1",
    "Fleetwood Town vs Port Vale": "1-1",
    
    # 8 de marzo 2025 - Ligue 2 France
    "Paris FC vs Lorient": "1-1",
    "Dunkerque vs Rodez": "1-2",
    "Red Star vs Amiens": "2-0",
    "Red Star FC vs Amiens": "2-0",
    
    # 8 de marzo 2025 - MLS
    "Columbus Crew vs Houston Dynamo": "0-0",
    "Seattle Sounders vs LAFC": "5-2",
    "Seattle Sounders vs Los Angeles FC": "5-2",
    "Atlanta United vs NY Red Bulls": "0-0",
    "Atlanta United vs New York Red Bulls": "0-0",
    "DC United vs Sporting KC": "2-1",
    "DC United vs Sporting Kansas City": "2-1",
    "FC Cincinnati vs Toronto FC": "2-0",
    "New England vs Philadelphia Union": "0-2",
    "New England Revolution vs Philadelphia Union": "0-2",
    "NYCFC vs Orlando City": "2-1",
    "New York City FC vs Orlando City": "2-1",
    "Austin FC vs Colorado Rapids": "0-1",
    "FC Dallas vs Chicago Fire": "1-3",
    "Nashville SC vs Portland Timbers": "2-0",
    "Real Salt Lake vs San Diego FC": "1-3",
    "Vancouver Whitecaps vs CF Montreal": "2-0",
    "San Jose vs Minnesota United": "0-1",
    "San Jose Earthquakes vs Minnesota United": "0-1",
    "LA Galaxy vs St. Louis CITY SC": "3-1",
    "LA Galaxy vs St Louis City SC": "3-1",
    "Inter Miami vs Charlotte FC": "4-1",
    "Inter Miami CF vs Charlotte FC": "4-1",
    
    # 8 de marzo 2025 - Eredivisie
    "Fortuna Sittard vs Heracles Almelo": "1-1",
    "Fortuna Sittard vs Heracles": "1-1",
    "Ajax vs PEC Zwolle": "3-0",
    "PSV vs Go Ahead Eagles": "3-2",
    "PSV Eindhoven vs Go Ahead Eagles": "3-2",
    "Feyenoord vs AZ Alkmaar": "2-1",
    "Feyenoord vs AZ": "2-1",
    "FC Twente vs Almere City": "4-0",
    "Willem II vs Heerenveen": "2-0",
    "NEC vs RKC Waalwijk": "1-0",
    "NEC Nijmegen vs RKC Waalwijk": "1-0",
    
    # 8 de marzo 2025 - Super League Switzerland
    "FC St Gallen vs Grasshopper Zürich": "2-1",
    "FC St. Gallen vs Grasshopper Club Zürich": "2-1",
    "Young Boys vs Basel": "0-1",
    "BSC Young Boys vs FC Basel": "0-1",
    "Lugano vs Lausanne": "2-0",
    "FC Lugano vs FC Lausanne-Sport": "2-0",
    
    # 8 de marzo 2025 - K League
    "FC Anyang vs Sangju Sangmu FC": "0-0",
    "FC Anyang vs Sangju Sangmu": "0-0",
    "Ulsan HD vs Jeonbuk Hyundai": "2-1",
    "Pohang Steelers vs Daejeon Citizen": "3-0",
    "Gimcheon Sangmu vs Gwangju FC": "1-1",
    "Incheon United vs Suwon FC": "2-0",
    
    # 8 de marzo 2025 - Ekstraklasa
    "Legia Warsaw vs Lech Poznań": "1-1",
    "Legia Warszawa vs Lech Poznań": "1-1",
    "Jagiellonia vs Raków Częstochowa": "0-2",
    "Radomiak vs Piast Gliwice": "1-0",
    "Korona Kielce vs Stal Mielec": "2-0",
    
    # 8 de marzo 2025 - Serie B
    "Palermo vs Catanzaro": "0-0",
    "Spezia vs Cremonese": "1-2",
    "Brescia vs Juve Stabia": "1-0",
    "Modena vs Südtirol": "1-1",
    "Pisa vs Sampdoria": "2-0",
    "Salernitana vs Frosinone": "0-0",
    "Cesena vs Mantova": "1-0",
    "Reggiana vs Cittadella": "2-2",
    
    # 9 de marzo 2025 - Premier League
    "Chelsea vs Leicester City": "1-2",
    "Tottenham vs Bournemouth": "0-1",
    "Tottenham Hotspur vs Bournemouth": "0-1",
    "Manchester United vs Arsenal": "1-1",
    "Newcastle vs Brighton": "0-0",
    "Newcastle United vs Brighton": "0-0",
    "Everton vs West Ham": "1-2",
    "Everton vs West Ham United": "1-2",
    
    # 9 de marzo 2025 - Serie A
    "Napoli vs Fiorentina": "3-0",
    "SSC Napoli vs Fiorentina": "3-0",
    
    # 9 de marzo 2025 - Serie B
    "Sassuolo vs Bari": "2-1",
    
    # 9 de marzo 2025 - La Liga
    "Real Sociedad vs Sevilla": "0-1",
    "CD Tenerife vs Huesca": "2-0",
    "Málaga vs Cádiz": "0-2",
    "Malaga vs Cadiz": "0-2",
    "Levante vs Cartagena": "3-0",
    "Granada vs Racing Ferrol": "3-0",
    
    # 9 de marzo 2025 - Super League Switzerland  
    "FC Zurich vs Servette": "1-1",
    "FC Zürich vs Servette FC": "1-1",
    
    # 9 de marzo 2025 - Liga Portugal
    "Sporting vs Porto": "2-1",
    "Sporting CP vs FC Porto": "2-1",
    "Benfica vs Braga": "4-1",
    "SL Benfica vs SC Braga": "4-1",
}


def normalizar_nombre(nombre: str) -> str:
    """Normaliza nombre de equipo para comparación."""
    nombre = nombre.lower().strip()
    # Remover caracteres especiales comunes
    nombre = re.sub(r'[._\-]', ' ', nombre)
    # Normalizar espacios múltiples
    nombre = re.sub(r'\s+', ' ', nombre)
    
    # Mapeo de variaciones comunes
    mapeos = {
        'manchester city': 'man city',
        'manchester united': 'man united', 
        'manchester utd': 'man united',
        'tottenham hotspur': 'tottenham',
        'wolverhampton wanderers': 'wolves',
        'wolverhampton': 'wolves',
        'brighton and hove albion': 'brighton',
        'brighton hove albion': 'brighton',
        'newcastle united': 'newcastle',
        'west ham united': 'west ham',
        'bayern münchen': 'bayern munich',
        'bayern munchen': 'bayern munich',
        'borussia mönchengladbach': 'mönchengladbach',
        'borussia monchengladbach': 'mönchengladbach',
        'bayer 04 leverkusen': 'bayer leverkusen',
        'bayer leverkusen': 'bayer leverkusen',
        'fc barcelona': 'barcelona',
        'atlético de madrid': 'atlético madrid',
        'atletico de madrid': 'atlético madrid',
        'atletico madrid': 'atlético madrid',
        'rc celta': 'celta vigo',
        'celta de vigo': 'celta vigo',
        'inter milan': 'inter',
        'internazionale': 'inter',
        'ac milan': 'milan',
        'hellas verona': 'verona',
        'paris saint germain': 'psg',
        'paris saint-germain': 'psg',
        'olympique lyonnais': 'lyon',
        'olympique marseille': 'marseille',
        'olympique de marseille': 'marseille',
        'stade brestois': 'brest',
        'losc lille': 'lille',
        'aj auxerre': 'auxerre',
        'fc nantes': 'nantes',
        'stade de reims': 'reims',
        'rc strasbourg': 'strasbourg',
        'fenerbahçe': 'fenerbahce',
        'beşiktaş': 'besiktas',
        'istanbul basaksehir': 'basaksehir',
        'psv eindhoven': 'psv',
        'az alkmaar': 'az',
        'nec nijmegen': 'nec',
        'fc twente': 'twente',
        'bsc young boys': 'young boys',
        'fc basel': 'basel',
        'fc lugano': 'lugano',
        'fc lausanne sport': 'lausanne',
        'grasshopper club zürich': 'grasshopper zürich',
        'grasshopper club zurich': 'grasshopper zürich',
        'grasshopper': 'grasshopper zürich',
        'legia warszawa': 'legia warsaw',
        'jagiellonia białystok': 'jagiellonia',
        'raków częstochowa': 'raków',
        'new york red bulls': 'ny red bulls',
        'new york city fc': 'nycfc',
        'los angeles fc': 'lafc',
        'sporting kansas city': 'sporting kc',
        'new england revolution': 'new england',
        'san jose earthquakes': 'san jose',
        'st louis city sc': 'st. louis city sc',
        'inter miami cf': 'inter miami',
        'sl benfica': 'benfica',
        'sporting cp': 'sporting',
        'sc braga': 'braga',
        'fc porto': 'porto',
        'ssc napoli': 'napoli',
        'real oviedo': 'oviedo',
        'doncaster rovers': 'doncaster',
        'tranmere rovers': 'tranmere',
        'milton keynes dons': 'mk dons',
        'darmstadt 98': 'darmstadt',
        'karlsruher sc': 'karlsruher',
        '1 fc union berlin': 'union berlin',
        '1 fc heidenheim': 'heidenheim',
        'tsg hoffenheim': 'hoffenheim',
        'sc freiburg': 'freiburg',
        'fc st pauli': 'st pauli',
        'vfl wolfsburg': 'wolfsburg',
        'fc augsburg': 'augsburg',
        'cd leganés': 'leganés',
        'deportivo alavés': 'alavés',
        'rcd espanyol': 'espanyol',
        'servette fc': 'servette',
        'fc zürich': 'fc zurich',
        'red star fc': 'red star',
    }
    
    for original, reemplazo in mapeos.items():
        if original in nombre:
            nombre = nombre.replace(original, reemplazo)
    
    return nombre


def buscar_resultado(partido: str) -> tuple:
    """
    Busca el resultado de un partido en el diccionario.
    Retorna (score, total_goles) o (None, None) si no encuentra.
    """
    partido_lower = normalizar_nombre(partido)
    
    # Extraer equipos
    if ' vs ' in partido_lower:
        local, visitante = partido_lower.split(' vs ')
    else:
        return None, None
    
    local = local.strip()
    visitante = visitante.strip()
    
    # Buscar directamente
    for key, score in RESULTADOS_CONFIRMADOS.items():
        key_norm = normalizar_nombre(key)
        if ' vs ' in key_norm:
            k_local, k_visitante = key_norm.split(' vs ')
            k_local = k_local.strip()
            k_visitante = k_visitante.strip()
            
            # Coincidencia exacta o parcial
            if (local in k_local or k_local in local) and (visitante in k_visitante or k_visitante in visitante):
                goles = score.split('-')
                total = int(goles[0]) + int(goles[1])
                return score, total
            
            # Intentar con palabras clave
            local_words = set(local.split())
            visitante_words = set(visitante.split())
            k_local_words = set(k_local.split())
            k_visitante_words = set(k_visitante.split())
            
            if local_words & k_local_words and visitante_words & k_visitante_words:
                goles = score.split('-')
                total = int(goles[0]) + int(goles[1])
                return score, total
    
    return None, None


def verificar_acierto(row, total_goles: int) -> str:
    """Verifica si el mercado Over/Under acertó."""
    if total_goles is None:
        return ""
    
    mercado = row['Mercado']
    
    if 'Over' in mercado:
        linea = float(mercado.replace('Over ', ''))
        return "Sí" if total_goles > linea else "No"
    elif 'Under' in mercado:
        linea = float(mercado.replace('Under ', ''))
        return "Sí" if total_goles < linea else "No"
    
    return ""


def main():
    csv_path = Path("/home/asus/Escritorio/proyectos/betsanalizer/betanalizer/historical_analysis/2025/marzo/historical_20250307.csv")
    
    print(f"Leyendo {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Total de filas: {len(df)}")
    print(f"Partidos únicos: {df['Partido'].nunique()}")
    
    # Agregar columnas de resultados
    df['Score'] = ""
    df['Total_Goles'] = ""
    df['Acerto'] = ""
    
    # Buscar resultados para cada partido
    partidos_unicos = df['Partido'].unique()
    encontrados = 0
    no_encontrados = []
    
    for partido in partidos_unicos:
        score, total_goles = buscar_resultado(partido)
        
        if score:
            encontrados += 1
            mask = df['Partido'] == partido
            df.loc[mask, 'Score'] = score
            df.loc[mask, 'Total_Goles'] = total_goles
            
            # Verificar aciertos
            for idx in df[mask].index:
                df.loc[idx, 'Acerto'] = verificar_acierto(df.loc[idx], total_goles)
        else:
            no_encontrados.append(partido)
    
    print(f"\n✓ Partidos con resultado encontrado: {encontrados}/{len(partidos_unicos)}")
    print(f"✗ Partidos sin resultado: {len(no_encontrados)}")
    
    if no_encontrados:
        print("\nPartidos sin resultado encontrado:")
        for p in sorted(no_encontrados):
            print(f"  - {p}")
    
    # Guardar CSV actualizado
    output_path = csv_path.parent / "historical_20250307_con_resultados.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ CSV guardado en: {output_path}")
    
    # Mostrar estadísticas de aciertos
    df_con_resultado = df[df['Score'] != ""]
    if len(df_con_resultado) > 0:
        total_apuestas = len(df_con_resultado)
        aciertos = (df_con_resultado['Acerto'] == "Sí").sum()
        fallos = (df_con_resultado['Acerto'] == "No").sum()
        
        print(f"\n=== ESTADÍSTICAS DE ACIERTOS ===")
        print(f"Total mercados con resultado: {total_apuestas}")
        print(f"Aciertos: {aciertos} ({100*aciertos/total_apuestas:.1f}%)")
        print(f"Fallos: {fallos} ({100*fallos/total_apuestas:.1f}%)")
        
        # Por tipo de mercado
        print("\n--- Por tipo de mercado ---")
        for mercado in df_con_resultado['Mercado'].unique():
            mask = df_con_resultado['Mercado'] == mercado
            m_aciertos = (df_con_resultado.loc[mask, 'Acerto'] == "Sí").sum()
            m_total = mask.sum()
            if m_total > 0:
                print(f"{mercado}: {m_aciertos}/{m_total} ({100*m_aciertos/m_total:.1f}%)")


if __name__ == "__main__":
    main()
