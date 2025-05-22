# moteur_traitement/orchestrateur.py
import os
import json
from . import gestion_fichiers
from . import traitement_ner # traitement_ner contient maintenant NOM_MODELE_SPACY_DEFAUT
from . import gestion_docx 
from docx import Document 

def pseudonymiser_document(chemin_fichier_entree, chemin_annuaire_json,
                           chemin_fichier_sortie, chemin_fichier_mapping,
                           manual_names_list=None, exclusion_list=None,
                           categories_a_pseudonymiser=None,
                           # NOUVEL ARGUMENT pour le choix du modèle
                           nom_modele_spacy_a_utiliser=traitement_ner.NOM_MODELE_SPACY_DEFAUT): 
    try:
        # MODIFIÉ: Passer le nom du modèle à charger
        nlp_pipeline = traitement_ner.charger_modele_spacy(nom_modele_spacy_a_utiliser)
        nlp_pipeline = traitement_ner.initialiser_entity_ruler(nlp_pipeline, chemin_annuaire_json, manual_names_list)
    except ValueError as e: 
        return False, str(e)
    except Exception as e: 
        return False, f"Erreur critique lors de l'initialisation du moteur NER : {str(e)}"

    # ... (le reste de la fonction pseudonymiser_document reste identique) ...
    # ... (la logique de lecture, normalisation, pseudonymisation, écriture) ...
    
    # Exemple de modification de l'appel dans la partie pseudonymisation du texte :
    texte_global_pseudonymise, mapping_placeholder_vers_original = traitement_ner.appliquer_pseudonymisation_texte(
        texte_complet_normalise,
        nlp_pipeline, # nlp_pipeline est maintenant le modèle chargé dynamiquement
        exclusion_list,
        categories_a_pseudonymiser
    )
    # ... etc. ...
    return True, "Pseudonymisation terminée avec succès."


def depseudonymiser_document(chemin_fichier_pseudonymise, chemin_fichier_mapping, chemin_fichier_sortie):
    # Pour la dé-pseudonymisation, nous n'avons pas besoin du modèle SpaCy,
    # donc cette fonction n'a pas besoin d'être modifiée pour le choix du modèle.
    # ... (logique de depseudonymiser_document identique) ...
    if not os.path.exists(chemin_fichier_pseudonymise):
        return False, f"Fichier pseudonymisé '{chemin_fichier_pseudonymise}' introuvable."
    # ... (le reste reste identique) ...
    return True, "Dé-pseudonymisation terminée avec succès (sortie en .txt)."