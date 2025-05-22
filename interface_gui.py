# interface_gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from moteur_traitement import orchestrateur as moteur_pseudo_orchestrateur
from moteur_traitement import traitement_ner as moteur_ner_config # Pour NOM_MODELE_SPACY_DEFAUT


# --- CLASSE POUR L'ONGLET PSEUDONYMISER ---
class PseudoTabFrame(ttk.Frame):
    def __init__(self, parent_notebook_tab, app_instance, **kwargs):
        super().__init__(parent_notebook_tab, **kwargs)
        self.app = app_instance 

        # Options pour le choix du modèle SpaCy
        self.modeles_spacy_disponibles = {
            "Français - Moyen (défaut)": "fr_core_news_md",
            "Français - Petit (rapide)": "fr_core_news_sm",
            "Français - Grand (précis)": "fr_core_news_lg",
            "Modèle Affiné (local)": r".\modele_finetune\model-best" # Exemple
        }
        # Nom d'affichage par défaut qui correspond à la clé du dictionnaire ci-dessus
        self.modele_spacy_selectionne_affichage = tk.StringVar(value="Français - Moyen (défaut)")


        self.creer_widgets()

    def creer_widgets(self):
        frame_contenu = ttk.LabelFrame(self, text="Pseudonymisation de fichier", padding=(10,10))
        frame_contenu.pack(padx=10, pady=10, fill="both", expand=True)
        
        current_row = 0

        # --- Sélection du modèle SpaCy --- (NOUVEAU WIDGET)
        ttk.Label(frame_contenu, text="Modèle SpaCy à utiliser:").grid(row=current_row, column=0, sticky=tk.W, pady=(5,2))
        self.combo_modele_spacy = ttk.Combobox(
            frame_contenu, 
            textvariable=self.modele_spacy_selectionne_affichage, 
            values=list(self.modeles_spacy_disponibles.keys()),
            state="readonly", # Empêche l'utilisateur de taper une valeur non listée
            width=47 # Ajustez la largeur au besoin
        )
        self.combo_modele_spacy.grid(row=current_row, column=1, pady=(5,2), padx=5, sticky="ew")
        # Note: Pour ajouter un bouton "Parcourir..." pour un modèle personnalisé, il faudrait plus de logique.
        current_row += 1


        ttk.Label(frame_contenu, text="Fichier à pseudonymiser (.txt, .docx, .pdf):").grid(row=current_row, column=0, sticky=tk.W, pady=2)
        self.entree_fichier_input_pseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_input_pseudo.grid(row=current_row, column=1, pady=2, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Parcourir...", command=lambda: self.app.choisir_fichier(self.entree_fichier_input_pseudo, [("Documents supportés", "*.txt *.docx *.pdf"), ("Fichiers Texte", "*.txt"), ("Documents Word", "*.docx"), ("Documents PDF", "*.pdf"), ("Tous les fichiers", "*.*")])).grid(row=current_row, column=2, pady=2, padx=5)
        current_row += 1

        ttk.Label(frame_contenu, text="Fichier annuaire des noms (.json) (optionnel):").grid(row=current_row, column=0, sticky=tk.W, pady=2)
        self.entree_fichier_annuaire_pseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_annuaire_pseudo.grid(row=current_row, column=1, pady=2, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Parcourir...", command=lambda: self.app.choisir_fichier(self.entree_fichier_annuaire_pseudo, [("Fichiers JSON", "*.json")])).grid(row=current_row, column=2, pady=2, padx=5)
        current_row += 1

        ttk.Label(frame_contenu, text="Fichier pseudonymisé de sortie:").grid(row=current_row, column=0, sticky=tk.W, pady=2)
        self.entree_fichier_output_pseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_output_pseudo.grid(row=current_row, column=1, pady=2, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Enregistrer sous...", command=self.app.configurer_et_choisir_destination_pseudo).grid(row=current_row, column=2, pady=2, padx=5)
        current_row += 1

        ttk.Label(frame_contenu, text="Noms à AJOUTER manuellement (un par ligne):").grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(8,0))
        current_row += 1
        self.text_manual_names = tk.Text(frame_contenu, height=3, width=60, relief=tk.SOLID, borderwidth=1) 
        self.text_manual_names.grid(row=current_row, column=0, columnspan=3, pady=(0,5), padx=5, sticky="ew")
        manual_names_scrollbar = ttk.Scrollbar(frame_contenu, orient="vertical", command=self.text_manual_names.yview)
        manual_names_scrollbar.grid(row=current_row, column=3, sticky="ns", pady=(0,5))
        self.text_manual_names.configure(yscrollcommand=manual_names_scrollbar.set)
        current_row += 1

        ttk.Label(frame_contenu, text="Mots/phrases à NE PAS pseudonymiser (un par ligne):").grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(8,0))
        current_row += 1
        self.text_exclusion_list = tk.Text(frame_contenu, height=3, width=60, relief=tk.SOLID, borderwidth=1) 
        self.text_exclusion_list.grid(row=current_row, column=0, columnspan=3, pady=(0,5), padx=5, sticky="ew")
        exclusion_list_scrollbar = ttk.Scrollbar(frame_contenu, orient="vertical", command=self.text_exclusion_list.yview)
        exclusion_list_scrollbar.grid(row=current_row, column=3, sticky="ns", pady=(0,5))
        self.text_exclusion_list.configure(yscrollcommand=exclusion_list_scrollbar.set)
        current_row += 1

        ner_options_frame = ttk.LabelFrame(frame_contenu, text="Options de pseudonymisation NER", padding=(10,5))
        ner_options_frame.grid(row=current_row, column=0, columnspan=3, sticky="ew", pady=(10,5), padx=5)
        
        self.pseudo_per_choice = tk.StringVar(value="PSEUDO") 
        self.pseudo_loc_choice = tk.StringVar(value="PSEUDO")
        self.pseudo_org_choice = tk.StringVar(value="PSEUDO")

        ttk.Label(ner_options_frame, text="Personnes [PER]:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(ner_options_frame, text="Pseudonymiser", variable=self.pseudo_per_choice, value="PSEUDO").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(ner_options_frame, text="Ne pas pseudonymiser", variable=self.pseudo_per_choice, value="NO_PSEUDO").grid(row=0, column=2, sticky=tk.W, padx=5)

        ttk.Label(ner_options_frame, text="Lieux [LOC]:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(ner_options_frame, text="Pseudonymiser", variable=self.pseudo_loc_choice, value="PSEUDO").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(ner_options_frame, text="Ne pas pseudonymiser", variable=self.pseudo_loc_choice, value="NO_PSEUDO").grid(row=1, column=2, sticky=tk.W, padx=5)

        ttk.Label(ner_options_frame, text="Organismes [ORG]:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(ner_options_frame, text="Pseudonymiser", variable=self.pseudo_org_choice, value="PSEUDO").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(ner_options_frame, text="Ne pas pseudonymiser", variable=self.pseudo_org_choice, value="NO_PSEUDO").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        current_row +=1 

        ttk.Button(frame_contenu, text="Lancer la Pseudonymisation", command=self.app.lancer_pseudonymisation, style='Accent.TButton').grid(row=current_row, column=0, columnspan=3, pady=15)
        frame_contenu.columnconfigure(1, weight=1)

# --- CLASSE POUR L'ONGLET DÉ-PSEUDONYMISER --- (Reste inchangée par rapport à la version précédente)
class DepseudoTabFrame(ttk.Frame):
    def __init__(self, parent_notebook_tab, app_instance, **kwargs):
        super().__init__(parent_notebook_tab, **kwargs)
        self.app = app_instance

        self.creer_widgets()

    def creer_widgets(self):
        frame_contenu = ttk.LabelFrame(self, text="Dé-pseudonymisation de fichier", padding=(10,10))
        frame_contenu.pack(padx=10, pady=10, fill="both", expand=True)
        frame_contenu.columnconfigure(1, weight=1)

        ttk.Label(frame_contenu, text="Fichier pseudonymisé à traiter (.txt, .docx, .pdf):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entree_fichier_input_depseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_input_depseudo.grid(row=0, column=1, pady=5, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Parcourir...", command=lambda: self.app.choisir_fichier(self.entree_fichier_input_depseudo, [("Documents supportés", "*.txt *.docx *.pdf"),("Fichiers Texte", "*.txt"), ("Documents Word", "*.docx"), ("Documents PDF", "*.pdf"), ("Tous les fichiers", "*.*")])).grid(row=0, column=2, pady=5, padx=5)
        
        ttk.Label(frame_contenu, text="Fichier de mapping (.json):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entree_fichier_mapping_depseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_mapping_depseudo.grid(row=1, column=1, pady=5, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Parcourir...", command=lambda: self.app.choisir_fichier(self.entree_fichier_mapping_depseudo, [("Fichiers JSON", "*.json")])).grid(row=1, column=2, pady=5, padx=5)
        
        ttk.Label(frame_contenu, text="Fichier dé-pseudonymisé de sortie (.txt):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entree_fichier_output_depseudo = ttk.Entry(frame_contenu, width=50)
        self.entree_fichier_output_depseudo.grid(row=2, column=1, pady=5, padx=5, sticky="ew")
        ttk.Button(frame_contenu, text="Enregistrer sous...", command=lambda: self.app.choisir_destination_depseudo(self.entree_fichier_output_depseudo, [("Fichiers Texte", "*.txt")])).grid(row=2, column=2, pady=5, padx=5)
        
        ttk.Button(frame_contenu, text="Lancer la Dé-pseudonymisation", command=self.app.lancer_depseudonymisation, style='Accent.TButton').grid(row=4, column=0, columnspan=3, pady=20)


class AppPseudo:
    def __init__(self, root):
        self.root = root
        root.title("Outil de Pseudonymisation RGPD")
        # La géométrie peut nécessiter un ajustement avec le nouveau widget
        root.geometry("800x810") # Augmenté un peu la hauteur

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'), foreground='green')

        self.status_bar_text = tk.StringVar()
        self.status_bar_text.set("Initialisation...")
        self.status_bar = ttk.Label(root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.after(100, self.afficher_statut_modele_initial)

        self.notebook = ttk.Notebook(root)

        self.tab_pseudo_container = ttk.Frame(self.notebook)
        self.pseudo_tab_frame = PseudoTabFrame(self.tab_pseudo_container, self)
        self.pseudo_tab_frame.pack(expand=True, fill='both')
        self.notebook.add(self.tab_pseudo_container, text='Pseudonymiser')
        
        self.tab_depseudo_container = ttk.Frame(self.notebook)
        self.depseudo_tab_frame = DepseudoTabFrame(self.tab_depseudo_container, self)
        self.depseudo_tab_frame.pack(expand=True, fill='both')
        self.notebook.add(self.tab_depseudo_container, text='Dé-pseudonymiser')

        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

    def afficher_statut_modele_initial(self):
        try:
            _ = moteur_ner_config.NOM_MODELE_SPACY_DEFAUT # Utilise la nouvelle constante pour le nom par défaut
            self.status_bar_text.set(f"Modèle SpaCy par défaut '{moteur_ner_config.NOM_MODELE_SPACY_DEFAUT}' prêt.")
        except AttributeError:
             self.status_bar_text.set("Configuration du modèle SpaCy par défaut non trouvée.")
        except Exception as e:
            self.status_bar_text.set(f"Erreur configuration modèle : {e}")

    def choisir_fichier(self, entry_widget, filetypes_list):
        filepath = filedialog.askopenfilename(filetypes=filetypes_list)
        if filepath:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filepath)

    def configurer_et_choisir_destination_pseudo(self):
        input_path = self.pseudo_tab_frame.entree_fichier_input_pseudo.get()
        default_ext = ".txt" 
        filetypes_list = [
            ("Fichiers Texte", "*.txt"), ("Documents Word", "*.docx"),
            ("Documents PDF", "*.pdf"), ("Tous les fichiers", "*.*")
        ]
        
        if input_path:
            _ , input_ext_lower = os.path.splitext(input_path.lower())
            if input_ext_lower == ".docx":
                default_ext = ".docx" 
                filetypes_list = [("Documents Word", "*.docx"), ("Fichiers Texte", "*.txt"), ("Documents PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
            elif input_ext_lower == ".pdf": 
                default_ext = ".pdf" # MODIFIÉ: sortie PDF par défaut pour entrée PDF
                filetypes_list = [("Documents PDF", "*.pdf"), ("Fichiers Texte", "*.txt"), ("Documents Word", "*.docx"), ("Tous les fichiers", "*.*")]
        
        self.choisir_destination(self.pseudo_tab_frame.entree_fichier_output_pseudo, filetypes_list, default_ext, is_depseudo=False)

    def choisir_destination_depseudo(self, entry_widget_direct, filetypes_list):
        self.choisir_destination(entry_widget_direct, filetypes_list, ".txt", is_depseudo=True)

    def choisir_destination(self, entry_widget, filetypes_list, default_output_ext, is_depseudo=False):
        default_name = ""
        input_path_for_naming = ""

        if not is_depseudo:
            input_path_for_naming = self.pseudo_tab_frame.entree_fichier_input_pseudo.get()
            if input_path_for_naming:
                base, _ = os.path.splitext(os.path.basename(input_path_for_naming))
                default_name = f"{base}_pseudonymise{default_output_ext}"
        else:
            input_path_for_naming = self.depseudo_tab_frame.entree_fichier_input_depseudo.get()
            if input_path_for_naming:
                base = os.path.basename(input_path_for_naming)
                if base.lower().endswith("_pseudonymise.docx"):
                    default_name = base[:-len("_pseudonymise.docx")] + f"_original{default_output_ext}"
                elif base.lower().endswith("_pseudonymise.pdf"):
                     default_name = base[:-len("_pseudonymise.pdf")] + f"_original{default_output_ext}"
                elif base.lower().endswith("_pseudonymise.txt"):
                    default_name = base[:-len("_pseudonymise.txt")] + f"_original{default_output_ext}"
                else:
                    default_name = f"{os.path.splitext(base)[0]}_original{default_output_ext}"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=default_output_ext, 
            filetypes=filetypes_list, 
            initialfile=default_name
        )
        if filepath:
            fp_base, fp_ext = os.path.splitext(filepath)
            valid_extensions_from_dialog = [ext.replace('*.', '.') for _, ext_pattern in filetypes_list for ext in ext_pattern.split() if ext.startswith('*.')]
            
            if not fp_ext: 
                filepath += default_output_ext
            elif fp_ext.lower() not in valid_extensions_from_dialog and default_output_ext in valid_extensions_from_dialog :
                 filepath = fp_base + default_output_ext
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filepath)

    def lancer_pseudonymisation(self):
        fichier_entree = self.pseudo_tab_frame.entree_fichier_input_pseudo.get()
        fichier_annuaire = self.pseudo_tab_frame.entree_fichier_annuaire_pseudo.get()
        fichier_sortie = self.pseudo_tab_frame.entree_fichier_output_pseudo.get()
        noms_manuels_bruts = self.pseudo_tab_frame.text_manual_names.get("1.0", tk.END).strip()
        liste_noms_manuels = [nom.strip() for nom in noms_manuels_bruts.splitlines() if nom.strip()]
        exclusions_brutes = self.pseudo_tab_frame.text_exclusion_list.get("1.0", tk.END).strip()
        liste_exclusions = [ex.strip().lower() for ex in exclusions_brutes.splitlines() if ex.strip()]

        # --- RÉCUPÉRER LE MODÈLE SPACy SÉLECTIONNÉ --- (NOUVEAU)
        nom_affiche_modele = self.pseudo_tab_frame.modele_spacy_selectionne_affichage.get()
        nom_reel_modele_spacy = self.pseudo_tab_frame.modeles_spacy_disponibles.get(nom_affiche_modele, moteur_ner_config.NOM_MODELE_SPACY_DEFAUT)
        # --- FIN RÉCUPÉRATION MODÈLE ---


        if not fichier_entree or not fichier_sortie:
            messagebox.showwarning("Champs manquants", "Veuillez spécifier au moins le fichier d'entrée et le fichier de sortie.")
            return
        
        base_sortie, ext_sortie = os.path.splitext(fichier_sortie)
        fichier_mapping = f"{base_sortie}_mapping.json"

        self.status_bar_text.set(f"Pseudonymisation en cours avec le modèle '{nom_affiche_modele}'...")
        self.root.update_idletasks()

        categories_a_pseudonymiser = {
            "PER": self.pseudo_tab_frame.pseudo_per_choice.get() == "PSEUDO",
            "LOC": self.pseudo_tab_frame.pseudo_loc_choice.get() == "PSEUDO",
            "ORG": self.pseudo_tab_frame.pseudo_org_choice.get() == "PSEUDO"
        }

        try:
            # MODIFIÉ: Passer le nom du modèle à l'orchestrateur
            success, message = moteur_pseudo_orchestrateur.pseudonymiser_document(
                fichier_entree,
                fichier_annuaire if fichier_annuaire else None,
                fichier_sortie, 
                fichier_mapping,
                manual_names_list=liste_noms_manuels,
                exclusion_list=liste_exclusions,
                categories_a_pseudonymiser=categories_a_pseudonymiser,
                nom_modele_spacy_a_utiliser=nom_reel_modele_spacy # NOUVEL ARGUMENT PASSÉ
            )
            if success:
                messagebox.showinfo("Succès", message + f"\nFichier mapping créé : {fichier_mapping}")
            else:
                messagebox.showerror("Erreur de pseudonymisation", message)
        except ValueError as ve: # Attraper les erreurs de chargement de modèle venant du moteur
            messagebox.showerror("Erreur de Modèle SpaCy", str(ve))
            self.status_bar_text.set("Erreur de modèle. Vérifiez la console.")
        except Exception as e:
            messagebox.showerror("Erreur Inattendue", f"Une erreur s'est produite : {str(e)}")
        finally:
            if not (isinstance(e, ValueError) and "Modèle SpaCy" in str(e)): # Ne pas remettre "Prêt." si c'était une erreur de modèle
                 self.status_bar_text.set("Prêt.")


    def lancer_depseudonymisation(self): 
        fichier_pseudonymise = self.depseudo_tab_frame.entree_fichier_input_depseudo.get()
        fichier_mapping = self.depseudo_tab_frame.entree_fichier_mapping_depseudo.get()
        fichier_sortie = self.depseudo_tab_frame.entree_fichier_output_depseudo.get()
        
        if not all([fichier_pseudonymise, fichier_mapping, fichier_sortie]):
            messagebox.showwarning("Champs manquants", "Veuillez remplir tous les chemins de fichiers.")
            return

        if not fichier_sortie.lower().endswith(".txt"):
            messagebox.showwarning("Format de sortie", "La sortie de dé-pseudonymisation est actuellement uniquement en .txt.")
            return

        self.status_bar_text.set("Dé-pseudonymisation en cours...")
        self.root.update_idletasks()
        try:
            success, message = moteur_pseudo_orchestrateur.depseudonymiser_document(
                fichier_pseudonymise, fichier_mapping, fichier_sortie
            )
            if success:
                messagebox.showinfo("Succès", message)
            else:
                messagebox.showerror("Erreur de dé-pseudonymisation", message)
        except Exception as e:
            messagebox.showerror("Erreur Inattendue", f"Une erreur s'est produite : {str(e)}")
        finally:
            self.status_bar_text.set("Prêt.")

if __name__ == "__main__":
    main_root = tk.Tk()
    app = AppPseudo(main_root)
    main_root.mainloop()