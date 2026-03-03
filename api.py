import io
import re
import numpy as np
from PIL import Image
from scipy.stats import entropy
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Advanced Synthetic Media Steganalysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_transition_rate(bit_array):
    """Berechnet, wie oft benachbarte Bits ihren Zustand wechseln (0->1 oder 1->0)."""
    if len(bit_array) < 2: return 0.0
    transitions = np.sum(bit_array[:-1] != bit_array[1:])
    return transitions / (len(bit_array) - 1)

def extract_smart_payload(lsb_flat, max_bytes=10000):
    chars = []
    for i in range(0, min(len(lsb_flat), max_bytes * 8) - 8, 8):
        byte_val = int("".join(map(str, lsb_flat[i:i+8])), 2)
        if 32 <= byte_val <= 126:
            chars.append(chr(byte_val))
        else:
            chars.append('.')
            
    raw_text = "".join(chars)
    words = re.findall(r'[A-Za-z0-9_]{5,}', raw_text)
    urls = re.findall(r'(https?://[^\s]+|[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', raw_text)
    base64_suspects = re.findall(r'(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', raw_text)

    return {
        "raw_snippet": raw_text[:800] + "..." if len(raw_text) > 800 else raw_text,
        "found_words": words[:10],
        "found_urls": urls,
        "base64_suspects": len(base64_suspects) > 0
    }

@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        # INNOVATION 1: Wir behalten die Farbkanäle (RGB), statt sie in Graustufen zu matschen!
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        pixel_data = np.array(img, dtype=np.int16)
        
        # Aufteilen in Farbkanäle (R, G, B)
        channel_entropies = []
        channel_transitions = []
        lsb_blue_flat = []
        
        for c in range(3):
            channel_data = pixel_data[:, :, c]
            lsb = channel_data & 1
            lsb_flat = lsb.flatten()
            
            # Entropie pro Kanal
            counts = np.bincount(lsb_flat)
            if len(counts) == 2:
                prob = counts / len(lsb_flat)
                ch_entropy = entropy(prob, base=2)
            else:
                ch_entropy = 0.0
                
            channel_entropies.append(ch_entropy)
            
            # INNOVATION 2: Transition Rate (Bit-Flip-Analyse)
            # Echter Krypto-Code nähert sich perfekt 0.5 an. Sensorrauschen weicht davon ab.
            ch_trans = calculate_transition_rate(lsb_flat)
            channel_transitions.append(ch_trans)
            
            if c == 2: # Wir merken uns den Blau-Kanal für die Text-Extraktion
                lsb_blue_flat = lsb_flat

        # Der höchste Entropie-Wert gewinnt (meistens Blau bei Steganographie)
        max_entropy = max(channel_entropies)
        
        # Prüfen, wie nah die Transition Rate an perfektem Zufall (0.5) ist
        # Je näher an 0 (also 0.5 - 0.5 = 0), desto verdächtiger!
        trans_deviation = abs(0.5 - channel_transitions[2]) # Wir prüfen den Blau-Kanal
        
        # INNOVATION 3: Smarte Anomalie-Berechnung
        # Hohe Entropie + Transition Rate extrem nah an 0.5 = Alarm!
        is_anomaly = False
        if max_entropy > 0.9998 and trans_deviation < 0.005:
            is_anomaly = True
            
        anomaly_score = max_entropy # Für das Frontend-Kompatibilität

        # Extrahiere Text bevorzugt aus dem Blau-Kanal
        extraction_results = extract_smart_payload(lsb_blue_flat)

        return {
            "filename": file.filename,
            "metrics": {
                "global_entropy": round(max_entropy, 6),
                "flat_region_entropy": round(max_entropy, 6), # Beibehalten für Frontend-Kompatibilität
                "anomaly_score": round(anomaly_score, 6),
                "blue_channel_transition_rate": round(channel_transitions[2], 6) # Neues, mächtiges Metrik-Feld
            },
            "anomaly_detected": is_anomaly,
            "extraction": extraction_results,
            "message": "🚨 SEVERE ANOMALY: Perfect cryptographic randomness detected in color channels (Steganography)." if is_anomaly else "✅ SAFE: Natural variance in bit transitions detected (Sensor Noise)."
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"status": "Advanced Steganalysis API (RGB & Transition-Aware) is operational.", "version": "3.0"}
