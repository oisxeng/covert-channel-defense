import argparse
import os
import numpy as np
from PIL import Image
from scipy.stats import entropy

def calculate_binary_entropy(data_array):
    """Berechnet die Shannon-Entropie eines binären Arrays."""
    # Zähle die Anzahl der 0en und 1en
    counts = np.bincount(data_array)
    # Berechne die Wahrscheinlichkeiten
    probabilities = counts / len(data_array)
    # Berechne die Entropie (Basis 2)
    return entropy(probabilities, base=2)

def analyze_image_lsb(image_path):
    """
    Extrahiert die Least Significant Bits (LSB) eines Bildes und 
    prüft sie auf steganographische Anomalien (zu hohe Entropie).
    """
    try:
        # Bild laden und in Graustufen umwandeln (macht die Analyse robuster)
        img = Image.open(image_path).convert('L')
        pixel_data = np.array(img)
        
        # Das LSB jedes Pixels extrahieren (Bitweise UND-Operation mit 1)
        lsb_matrix = pixel_data & 1
        
        # Matrix in ein 1D-Array glätten
        lsb_flat = lsb_matrix.flatten()
        
        # Entropie berechnen
        lsb_entropy = calculate_binary_entropy(lsb_flat)
        
        return lsb_entropy
    except Exception as e:
        print(f"Fehler bei der Bildanalyse: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="AI Slop Anomaly Detector (Steganalysis)")
    parser.add_argument("--image", type=str, help="Pfad zum Bild, das auf versteckte Payloads geprüft werden soll.")
    # Der Schwellenwert (Threshold) ab wann Alarm geschlagen wird. 
    # Perfekter Zufall = 1.0. Stego-Bilder liegen oft bei > 0.999
    parser.add_argument("--threshold", type=float, default=0.999, help="Entropie-Schwellenwert für Alarm (0.0 bis 1.0)")
    
    args = parser.parse_args()
    
    print("=== 🕵️‍♂️ AI Slop Anomaly Detector (Steganalysis) ===\n")
    
    if args.image:
        if not os.path.exists(args.image):
            print(f"Datei nicht gefunden: {args.image}")
            return
            
        print(f"[1] Analysiere Bild: '{args.image}'")
        print("[2] Extrahiere Least Significant Bits (LSB)...")
        
        lsb_entropy = analyze_image_lsb(args.image)
        
        if lsb_entropy is not None:
            print(f"\n[3] LSB Entropie-Wert: {lsb_entropy:.6f} (Maximal: 1.0)")
            
            if lsb_entropy >= args.threshold:
                print("\n[🚨 ALARM] Anomalie erkannt!")
                print("    Das Pixelrauschen ist unnatürlich zufällig. Dies ist ein starkes")
                print("    Indiz für eingebettete steganographische KI-Payloads (Data Poisoning).")
            else:
                print("\n[✓] Keine Anomalie.")
                print("    Das Bild weist natürliche strukturelle Rauschmuster auf.")
    else:
        print("Bitte gib eine Datei an. Beispiel: python slop_detector.py --image verdacht.png")

if __name__ == "__main__":
    main()
