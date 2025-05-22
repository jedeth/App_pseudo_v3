# moteur_traitement/traitement_ner.py
import spacy
import json
import os # Nécessaire pour os.path.exists

# Constante pour le nom du modèle SpaCy à utiliser
NOM_MODELE_SPACY = "fr_core_news_md" # Vous pourrez changer cela si vous utilisez un modèle affiné plus tard

# Variable globale pour stocker le pipeline NLP une fois chargé, afin d'éviter de le recharger à chaque appel.
NLP_PIPELINE = None

def charger_modele_spacy():
    """
    Charge le modèle SpaCy s'il n'est pas déjà chargé.
    Retourne le pipeline NLP chargé.
    """
    global NLP_PIPELINE
    if NLP_PIPELINE is None:
        try:
            NLP_PIPELINE = spacy.load(NOM_MODELE_SPACY)
            print(f"Modèle SpaCy '{NOM_MODELE_SPACY}' chargé.")
        except OSError:
            # Erreur si le modèle n'est pas trouvé (non téléchargé)
            message_erreur = (
                f"Modèle SpaCy '{NOM_MODELE_SPACY}' non trouvé.\n"
                f"Veuillez l'installer en ouvrant une invite de commande (avec votre environnement virtuel activé) et en tapant :\n"
                f"python -m spacy download {NOM_MODELE_SPACY}"
            )
            print(message_erreur)
            # Lever une exception pour que l'orchestrateur puisse l'attraper et informer l'utilisateur
            raise ValueError(message_erreur) 
    return NLP_PIPELINE

def initialiser_entity_ruler(nlp_instance, chemin_annuaire_json, manual_names_list=None):
    """
    Initialise ou réinitialise l'Entity Ruler dans le pipeline SpaCy avec les patterns
    provenant d'un fichier annuaire JSON et/ou d'une liste de noms manuels.
    Toutes les entrées sont considérées comme des "PER" (Personnes).
    """
    patterns = []

    # Chargement depuis le fichier annuaire JSON
    if chemin_annuaire_json:
        if not os.path.exists(chemin_annuaire_json):
            print(f"Avertissement : Le fichier annuaire JSON '{chemin_annuaire_json}' est introuvable.")
        else:
            try:
                with open(chemin_annuaire_json, 'r', encoding='utf-8') as f:
                    annuaire_data = json.load(f)
                if not isinstance(annuaire_data, list):
                    print(f"Avertissement : Le contenu de l'annuaire JSON '{chemin_annuaire_json}' n'est pas une liste.")
                else:
                    for entree in annuaire_data:
                        if not isinstance(entree, dict): continue
                        prenom = entree.get("prenom", "").strip()
                        nom = entree.get("nom", "").strip()
                        
                        nom_complet = f"{prenom} {nom}".strip() if prenom and nom else prenom if prenom else nom
                        
                        if nom_complet:
                            pattern = [{"LOWER": mot.lower()} for mot in nom_complet.split()]
                            if pattern: # S'assurer que le pattern n'est pas vide
                                patterns.append({"label": "PER", "pattern": pattern})
            except json.JSONDecodeError:
                print(f"Avertissement : Le fichier annuaire JSON '{chemin_annuaire_json}' n'est pas un JSON valide.")
            except Exception as e:
                print(f"Avertissement : Erreur lors du traitement de l'annuaire JSON '{chemin_annuaire_json}': {e}")

    # Ajout depuis la liste de noms manuels
    if manual_names_list:
        print(f"Ajout de {len(manual_names_list)} nom(s) manuel(s) à l'EntityRuler.")
        for nom_complet_manuel in manual_names_list:
            nom_complet = nom_complet_manuel.strip()
            if nom_complet:
                pattern = [{"LOWER": mot.lower()} for mot in nom_complet.split()]
                if pattern:
                    # Éviter les doublons de patterns exacts
                    is_duplicate = any(p["pattern"] == pattern and p["label"] == "PER" for p in patterns)
                    if not is_duplicate:
                        patterns.append({"label": "PER", "pattern": pattern})
    
    # Retirer l'ancien ruler s'il existe, avant d'en ajouter un nouveau (ou pas)
    if "entity_ruler" in nlp_instance.pipe_names:
        nlp_instance.remove_pipe("entity_ruler")
        print("Ancien EntityRuler retiré.")

    if patterns:
        # Ajouter l'Entity Ruler avant le composant "ner"
        # overwrite_ents=True signifie que les entités du ruler écraseront celles du modèle statistique
        ruler = nlp_instance.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
        ruler.add_patterns(patterns)
        print(f"{len(patterns)} règle(s) au total (label PER) ajoutée(s) à l'EntityRuler.")
    else:
        print("Avertissement : Aucun pattern (ni de l'annuaire, ni manuel) n'a été fourni ou trouvé. L'EntityRuler ne sera pas utilisé.")
        
    return nlp_instance

def appliquer_pseudonymisation_texte(texte_a_traiter, nlp_pipeline, exclusion_list=None, categories_a_pseudonymiser=None):
    """
    Applique la pseudonymisation sur une chaîne de texte.
    Retourne le texte pseudonymisé et un dictionnaire de mapping (placeholder -> texte_original).
    """
    if categories_a_pseudonymiser is None:
        # Par défaut, pseudonymiser PER, LOC, ORG si non spécifié
        categories_a_pseudonymiser = {"PER": True, "LOC": True, "ORG": True}

    doc = nlp_pipeline(texte_a_traiter)
    texte_modifie_liste_chars = list(texte_a_traiter) 
    correspondances = {} # Dictionnaire pour stocker: placeholder -> texte_original
    compteurs_placeholders_par_type = {} 

    exclusion_set = set(ex.lower() for ex in exclusion_list) if exclusion_list else set()

    # Trier les entités par leur caractère de fin, en ordre décroissant (de la fin vers le début du texte)
    # Cela évite les problèmes de décalage d'indices lors des remplacements dans la liste de caractères.
    entites_triees = sorted(doc.ents, key=lambda e: e.end_char, reverse=True)

    for ent in entites_triees:
        # Vérifier si l'entité doit être exclue
        if ent.text.lower() in exclusion_set:
            print(f"INFO: Entité '{ent.text}' ({ent.label_}) ignorée car dans la liste d'exclusion.")
            continue

        # Vérifier si la catégorie de l'entité doit être pseudonymisée
        if ent.label_ in categories_a_pseudonymiser and categories_a_pseudonymiser.get(ent.label_, False):
            label_pour_placeholder = ent.label_ 
            
            # Incrémenter le compteur pour ce type d'entité
            compteurs_placeholders_par_type[label_pour_placeholder] = compteurs_placeholders_par_type.get(label_pour_placeholder, 0) + 1
            
            placeholder = f"[{label_pour_placeholder.upper()}_{compteurs_placeholders_par_type[label_pour_placeholder]}]"
            
            # Enregistrer la correspondance (placeholder -> texte original)
            correspondances[placeholder] = ent.text
            
            # Remplacer le texte original par le placeholder dans la liste de caractères
            texte_modifie_liste_chars[ent.start_char:ent.end_char] = list(placeholder)
            
    return "".join(texte_modifie_liste_chars), correspondances