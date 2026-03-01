import math
import random
import argparse
from collections import Counter
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Lade NLTK Ressourcen sicher herunter
def setup_nltk():
    resources = ['punkt', 'wordnet', 'averaged_perceptron_tagger']
    for res in resources:
        try:
            nltk.data.find(f'tokenizers/{res}' if res == 'punkt' else f'corpora/{res}')
        except LookupError:
            nltk.download(res, quiet=True)

setup_nltk()

def get_wordnet_pos(treebank_tag):
    """
    Übersetzt die NLTK POS-Tags in WordNet POS-Tags.
    Das sorgt dafür, dass Verben nur durch Verben und Nomen nur durch Nomen ersetzt werden.
    """
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def calculate_entropy(text, level='word'):
    """
    Berechnet die Shannon-Entropie des Textes.
    Unterstützt Zeichen-Ebene ('char') oder Wort-Ebene ('word' / Tokens).
    """
    if not text:
        return 0.0
        
    if level == 'word':
        elements = word_tokenize(text.lower())
    else:
        elements = list(text)
        
    probabilities = [count / len(elements) for element, count in Counter(elements).items()]
    entropy = -sum(p * math.log2(p) for p in probabilities)
    return round(entropy, 4)

def apply_semantic_perturbation(text, perturbation_rate=0.2):
    """
    Wendet semantisch erhaltende Perturbation an, um steganographische Kanäle zu stören.
    Nutzt POS-Tagging für grammatikalisch korrekte Synonym-Ersetzungen.
    """
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)
    perturbed_words = []
    
    for word, tag in tagged_tokens:
        # Nur alphabetische Wörter stören, Rate prüfen
        if word.isalpha() and random.random() < perturbation_rate:
            wn_tag = get_wordnet_pos(tag)
            if wn_tag:
                # Suche nach Synonymen mit exakt derselben Wortart
                synsets = wordnet.synsets(word, pos=wn_tag)
                if synsets:
                    lemmas = []
                    for synset in synsets:
                        for lemma in synset.lemma_names():
                            if lemma.lower() != word.lower() and '_' not in lemma:
                                lemmas.append(lemma)
                    
                    if lemmas:
                        # Behalte die Groß-/Kleinschreibung des Originals bei
                        chosen = random.choice(lemmas)
                        if word.istitle():
                            chosen = chosen.capitalize()
                        perturbed_words.append(chosen)
                        continue
                        
        perturbed_words.append(word)
        
    # Setze den Text wieder zusammen (simpel)
    # Für produktiven Einsatz würde man hier Detokenization nutzen (z.B. MosesDetokenizer)
    return " ".join(perturbed_words).replace(" ,", ",").replace(" .", ".").replace(" !", "!")

def main():
    parser = argparse.ArgumentParser(description="AI Slop Steganography Defense Toolkit")
    parser.add_argument("--text", type=str, help="Der zu analysierende Text. Wenn leer, wird ein Beispiel verwendet.")
    parser.add_argument("--rate", type=float, default=0.25, help="Wahrscheinlichkeit für Synonym-Ersetzung (0.0 bis 1.0).")
    args = parser.parse_args()

    print("=== 🛡️ AI Slop Steganography Defense Toolkit ===\n")
    
    text = args.text if args.text else (
        "The quick implementation of advanced neural networks completely transforms "
        "digital landscapes. Technology rapidly evolves."
    )
    
    print("[1] Original Text:")
    print(text)
    
    word_entropy = calculate_entropy(text, level='word')
    char_entropy = calculate_entropy(text, level='char')
    print(f"\n[2] Entropy Analysis:")
    print(f"    - Word-Level Entropy: {word_entropy} bits/word")
    print(f"    - Char-Level Entropy: {char_entropy} bits/char")
    
    print(f"\n[3] Applying Semantic Perturbation (Rate: {args.rate * 100}%)...")
    sanitized_text = apply_semantic_perturbation(text, perturbation_rate=args.rate)
    
    print("\n[4] Sanitized Output Data:")
    print(sanitized_text)
    print("\n[✓] Fragile steganographic channels have been disrupted.")

if __name__ == "__main__":
    main()
