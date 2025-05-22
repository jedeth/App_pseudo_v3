# moteur_traitement/orchestrateur.py
import os
import json
# from tkinter import messagebox # Le moteur ne devrait pas directement interagir avec Tkinter messagebox
from . import gestion_fichiers
from . import traitement_ner
from . import gestion_docx 
from docx import Document 

# Variable globale pour le pipeline NLP, gérée par traitement_ner
# traitement_ner.NLP_PIPELINE sera initialisé par charger_modele_spacy()


def pseudonymiser_document(chemin_fichier_entree, chemin_annuaire_json,
                           chemin_fichier_sortie, chemin_fichier_mapping,
                           manual_names_list=None, exclusion_list=None,
                           categories_a_pseudonymiser=None,
                           nom_modele_spacy_a_utiliser=traitement_ner.NOM_MODELE_SPACY_DEFAUT): # Ajout du choix de modèle
    try:
        nlp_pipeline = traitement_ner.charger_modele_spacy(nom_modele_spacy_a_utiliser) # Utilisation du modèle demandé
        nlp_pipeline = traitement_ner.initialiser_entity_ruler(nlp_pipeline, chemin_annuaire_json, manual_names_list)
    except ValueError as e: 
        return False, str(e)
    except Exception as e: 
        return False, f"Erreur critique lors de l'initialisation du moteur NER : {str(e)}"

    if not os.path.exists(chemin_fichier_entree):
        return False, f"Fichier d'entrée '{chemin_fichier_entree}' introuvable."

    nom_fichier_entree_base, extension_fichier_entree = os.path.splitext(chemin_fichier_entree)
    extension_fichier_entree = extension_fichier_entree.lower()

    print(f"DEBUG Orchestrateur: Fichier d'entrée reçu: '{chemin_fichier_entree}'")
    print(f"DEBUG Orchestrateur: Extension détectée (après .lower()): '{extension_fichier_entree}'")

    texte_complet_original_brut = ""
    try:
        if extension_fichier_entree == ".txt":
            texte_complet_original_brut = gestion_fichiers.lire_contenu_txt(chemin_fichier_entree)
        elif extension_fichier_entree == ".docx":
            texte_complet_original_brut = gestion_fichiers.lire_contenu_docx_texte_complet(chemin_fichier_entree)
        elif extension_fichier_entree == ".pdf":
            texte_complet_original_brut = gestion_fichiers.lire_contenu_pdf_texte_complet(chemin_fichier_entree)
        else:
            return False, f"Type de fichier d'entrée non supporté : '{extension_fichier_entree}'. Uniquement .txt, .docx et .pdf sont acceptés."
    except ValueError as ve: 
        return False, str(ve)
    except Exception as e:
         return False, f"Erreur inattendue lors de la lecture du fichier '{chemin_fichier_entree}': {str(e)}"

    # DÉFINITION DE texte_complet_normalise
    texte_complet_normalise = gestion_fichiers.normaliser_texte(texte_complet_original_brut)

    # --- PASSE 1: Pseudonymisation globale du texte extrait ---
    texte_global_pseudonymise, mapping_placeholder_vers_original = traitement_ner.appliquer_pseudonymisation_texte(
        texte_complet_normalise, # Maintenant cette variable existe
        nlp_pipeline,
        exclusion_list,
        categories_a_pseudonymiser
    )
    
    mapping_original_vers_placeholder_trie = dict(
        sorted({v: k for k, v in mapping_placeholder_vers_original.items()}.items(), 
               key=lambda item: len(item[0]), 
               reverse=True)
    )

    # --- PASSE 2: Écriture du fichier de sortie ---
    nom_fichier_sortie_base, extension_fichier_sortie = os.path.splitext(chemin_fichier_sortie)
    extension_fichier_sortie = extension_fichier_sortie.lower()

    try:
        if extension_fichier_sortie == ".docx":
            if extension_fichier_entree == ".pdf":
                print("Avertissement: Entrée PDF avec sortie DOCX demandée. Création d'un DOCX simple avec le texte extrait.")
                gestion_fichiers.sauvegarder_document_docx_simple(chemin_fichier_sortie, texte_global_pseudonymise)
            elif extension_fichier_entree == ".docx": 
                doc_sortie_vide = Document() 
                gestion_docx.reconstruire_docx_pseudonymise(
                    chemin_fichier_entree, 
                    doc_sortie_vide,
                    mapping_original_vers_placeholder_trie,
                    nlp_pipeline, 
                    exclusion_list, 
                    categories_a_pseudonymiser
                )
                doc_sortie_vide.save(chemin_fichier_sortie)
                print(f"Fichier DOCX pseudonymisé (avec structure) sauvegardé sous : {chemin_fichier_sortie}")
            else: # Entrée TXT vers sortie DOCX (simple)
                 gestion_fichiers.sauvegarder_document_docx_simple(chemin_fichier_sortie, texte_global_pseudonymise)

        elif extension_fichier_sortie == ".pdf":
            gestion_fichiers.sauvegarder_document_pdf_simple(chemin_fichier_sortie, texte_global_pseudonymise)

        elif extension_fichier_sortie == ".txt":
            gestion_fichiers.sauvegarder_fichier_txt(chemin_fichier_sortie, texte_global_pseudonymise)
        else:
            return False, f"Format de fichier de sortie non supporté : '{extension_fichier_sortie}'. L'interface devrait garantir .txt, .docx ou .pdf."
    except IOError as ioe: 
        return False, str(ioe)
    except Exception as e:
        return False, f"Erreur inattendue lors de l'écriture du fichier pseudonymisé '{chemin_fichier_sortie}': {str(e)}"

    try:
        dossier_mapping = os.path.dirname(chemin_fichier_mapping)
        if dossier_mapping and not os.path.exists(dossier_mapping):
            os.makedirs(dossier_mapping)
        with open(chemin_fichier_mapping, 'w', encoding='utf-8') as f_map:
            json.dump(mapping_placeholder_vers_original, f_map, ensure_ascii=False, indent=4)
    except Exception as e:
        return False, f"Erreur lors de l'écriture du fichier de mapping : {str(e)}"
    
    return True, "Pseudonymisation terminée avec succès."


def depseudonymiser_document(chemin_fichier_pseudonymise, chemin_fichier_mapping, chemin_fichier_sortie):
    # ... (logique de dé-pseudonymisation existante) ...
    # ... (identique à la version que vous avez déjà et qui fonctionnait) ...
    if not os.path.exists(chemin_fichier_pseudonymise):
        return False, f"Fichier pseudonymisé '{chemin_fichier_pseudonymise}' introuvable."
    if not os.path.exists(chemin_fichier_mapping):
        return False, f"Fichier de mapping '{chemin_fichier_mapping}' introuvable."
    
    nom_f_pseudo, ext_f_pseudo = os.path.splitext(chemin_fichier_pseudonymise)
    ext_f_pseudo = ext_f_pseudo.lower()
    contenu_pseudonymise_brut = ""

    try:
        if ext_f_pseudo == ".docx":
            contenu_pseudonymise_brut = gestion_fichiers.lire_contenu_docx_texte_complet(chemin_fichier_pseudonymise)
        elif ext_f_pseudo == ".txt":
            contenu_pseudonymise_brut = gestion_fichiers.lire_contenu_txt(chemin_fichier_pseudonymise)
        elif ext_f_pseudo == ".pdf": 
            contenu_pseudonymise_brut = gestion_fichiers.lire_contenu_pdf_texte_complet(chemin_fichier_pseudonymise)
        else:
            return False, f"Format de fichier d'entrée pour dé-pseudonymisation non supporté: {ext_f_pseudo}"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erreur lors de la lecture du fichier pseudonymisé '{chemin_fichier_pseudonymise}': {str(e)}"

    try:
        with open(chemin_fichier_mapping, 'r', encoding='utf-8') as f_map:
            mapping_placeholder_vers_original = json.load(f_map)
    except Exception as e:
        return False, f"Erreur lors de la lecture du fichier de mapping : {str(e)}"

    if not isinstance(mapping_placeholder_vers_original, dict):
        return False, "Format de fichier de mapping incorrect."
    
    contenu_depseudonymise = contenu_pseudonymise_brut
    for placeholder, original_text in sorted(mapping_placeholder_vers_original.items(), key=lambda item: len(item[0]), reverse=True):
        contenu_depseudonymise = contenu_depseudonymise.replace(placeholder, original_text)
    
    try:
        gestion_fichiers.sauvegarder_fichier_txt(chemin_fichier_sortie, contenu_depseudonymise)
        print(f"Fichier dé-pseudonymisé sauvegardé sous (format TXT) : {chemin_fichier_sortie}")
    except IOError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erreur lors de l'écriture du fichier dé-pseudonymisé : {str(e)}"
        
    return True, "Dé-pseudonymisation terminée avec succès (sortie en .txt)."