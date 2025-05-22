# moteur_traitement/traitement_ner.py
import spacy
import json
import os

# Nom du modèle SpaCy par défaut si aucun n'est spécifié
NOM_MODELE_SPACY_DEFAUT = "fr_core_news_md" 

# Variables globales pour stocker le pipeline NLP chargé et le nom du modèle actuellement chargé
NLP_PIPELINE = None
MODELE_ACTUELLEMENT_CHARGE = None # Stocke le nom/chemin du modèle dans NLP_PIPELINE

def charger_modele_spacy(nom_modele_demande=NOM_MODELE_SPACY_DEFAUT):
    """
    Charge un modèle SpaCy spécifié s'il n'est pas déjà chargé ou si un modèle différent est demandé.
    nom_modele_demande: Peut être un nom de package SpaCy (ex: "fr_core_news_md") 
                        ou un chemin vers un modèle sauvegardé.
    Retourne le pipeline NLP chargé.
    """
    global NLP_PIPELINE, MODELE_ACTUELLEMENT_CHARGE

    # Si aucun pipeline n'est chargé OU si le modèle demandé est différent de celui chargé
    if NLP_PIPELINE is None or nom_modele_demande != MODELE_ACTUELLEMENT_CHARGE:
        print(f"Tentative de chargement du modèle SpaCy : '{nom_modele_demande}'...")
        try:
            NLP_PIPELINE = spacy.load(nom_modele_demande)
            MODELE_ACTUELLEMENT_CHARGE = nom_modele_demande # Mettre à jour le nom du modèle chargé
            print(f"Modèle SpaCy '{MODELE_ACTUELLEMENT_CHARGE}' chargé avec succès.")
        except OSError as e:
            # Erreur si le modèle n'est pas trouvé (nom incorrect, non téléchargé, ou chemin invalide)
            message_erreur = (
                f"Modèle SpaCy '{nom_modele_demande}' introuvable ou invalide.\n"
                f"Détails de l'erreur : {e}\n"
                f"Si c'est un modèle standard (ex: fr_core_news_sm, fr_core_news_lg), "
                f"veuillez l'installer via :\n"
                f"python -m spacy download {nom_modele_demande}\n"
                f"Si c'est un modèle personnalisé, vérifiez le chemin d'accès."
            )
            print(message_erreur)
            # Rétablir NLP_PIPELINE et MODELE_ACTUELLEMENT_CHARGE à None si le chargement échoue
            NLP_PIPELINE = None
            MODELE_ACTUELLEMENT_CHARGE = None
            raise ValueError(message_erreur)
        except Exception as e_gen: # Autres erreurs potentielles
            NLP_PIPELINE = None
            MODELE_ACTUELLEMENT_CHARGE = None
            print(f"Une erreur inattendue est survenue lors du chargement du modèle '{nom_modele_demande}': {e_gen}")
            raise ValueError(f"Erreur chargement modèle '{nom_modele_demande}': {e_gen}")
            
    elif NLP_PIPELINE is not None and nom_modele_demande == MODELE_ACTUELLEMENT_CHARGE:
        print(f"Modèle SpaCy '{MODELE_ACTUELLEMENT_CHARGE}' déjà chargé.")
        
    return NLP_PIPELINE

# La constante NOM_MODELE_SPACY n'est plus utilisée directement par charger_modele_spacy
# mais peut rester comme un défaut pour l'orchestrateur ou l'interface.
# La variable NLP (nom précédent de NLP_PIPELINE) n'est plus nécessaire ici.

def initialiser_entity_ruler(nlp_instance, chemin_annuaire_json, manual_names_list=None):
    # ... (Cette fonction reste identique, elle opère sur l'nlp_instance fournie) ...
    patterns = []
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
                            if pattern:
                                patterns.append({"label": "PER", "pattern": pattern})
            except json.JSONDecodeError:
                print(f"Avertissement : Le fichier annuaire JSON '{chemin_annuaire_json}' n'est pas un JSON valide.")
            except Exception as e:
                print(f"Avertissement : Erreur lors du traitement de l'annuaire JSON '{chemin_annuaire_json}': {e}")

    if manual_names_list:
        print(f"Ajout de {len(manual_names_list)} nom(s) manuel(s) à l'EntityRuler.")
        for nom_complet_manuel in manual_names_list:
            nom_complet = nom_complet_manuel.strip()
            if nom_complet:
                pattern = [{"LOWER": mot.lower()} for mot in nom_complet.split()]
                if pattern:
                    is_duplicate = any(p["pattern"] == pattern and p["label"] == "PER" for p in patterns)
                    if not is_duplicate:
                        patterns.append({"label": "PER", "pattern": pattern})
    
    if "entity_ruler" in nlp_instance.pipe_names:
        nlp_instance.remove_pipe("entity_ruler")
        print("Ancien EntityRuler retiré.")

    if patterns:
        ruler = nlp_instance.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
        ruler.add_patterns(patterns)
        print(f"{len(patterns)} règle(s) au total (label PER) ajoutée(s) à l'EntityRuler.")
    else:
        print("Avertissement : Aucun pattern (ni de l'annuaire, ni manuel) n'a été fourni ou trouvé. L'EntityRuler ne sera pas utilisé.")
        
    return nlp_instance

def appliquer_pseudonymisation_texte(texte_a_traiter, nlp_pipeline, exclusion_list=None, categories_a_pseudonymiser=None):
    # ... (Cette fonction reste identique) ...
    if categories_a_pseudonymiser is None:
        categories_a_pseudonymiser = {"PER": True, "LOC": True, "ORG": True}

    doc = nlp_pipeline(texte_a_traiter)
    texte_modifie_liste_chars = list(texte_a_traiter) 
    correspondances = {} 
    compteurs_placeholders_par_type = {} 

    exclusion_set = set(ex.lower() for ex in exclusion_list) if exclusion_list else set()
    entites_triees = sorted(doc.ents, key=lambda e: e.end_char, reverse=True)

    for ent in entites_triees:
        if ent.text.lower() in exclusion_set:
            # print(f"INFO: Entité '{ent.text}' ({ent.label_}) ignorée car dans la liste d'exclusion.")
            continue

        if ent.label_ in categories_a_pseudonymiser and categories_a_pseudonymiser.get(ent.label_, False):
            label_pour_placeholder = ent.label_ 
            compteurs_placeholders_par_type[label_pour_placeholder] = compteurs_placeholders_par_type.get(label_pour_placeholder, 0) + 1
            placeholder = f"[{label_pour_placeholder.upper()}_{compteurs_placeholders_par_type[label_pour_placeholder]}]"
            correspondances[placeholder] = ent.text
            texte_modifie_liste_chars[ent.start_char:ent.end_char] = list(placeholder)
            
    return "".join(texte_modifie_liste_chars), correspondances