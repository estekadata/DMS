# Mise à jour DMS Multirex — Guide client

## En quelques mots

Le système se compose de **2 outils complémentaires** :

| Outil | Rôle | Utilisation |
|---|---|---|
| 🌐 **Site web** ([dms-frontend-phi-six.vercel.app](https://dms-frontend-phi-six.vercel.app)) | **Visualiser et exploiter** les données (recherche moteurs, ventes, réservations, analyses, etc.) | Quotidien, depuis n'importe quel navigateur |
| 💻 **App de mise à jour** (`MultirexDMS_Updater.exe`) | **Synchroniser** les nouvelles données depuis Access vers Supabase | À chaque export Access (1× / semaine ou plus selon vos besoins) |

Les deux tapent sur la **même base Supabase**. Quand vous mettez à jour, les changements sont visibles immédiatement sur le site.

> 💡 **Synchro automatique (recommandé)** : pour ne plus avoir à lancer l'outil à la main,
> une tâche planifiée peut synchroniser la base toute seule (au démarrage du PC + chaque jour).
> Voir **[AUTOSYNC.md](AUTOSYNC.md)** (mise en place par l'équipe technique).

---

## Comment mettre à jour les données

### Étape 1 — Exporter votre base Access
Vous avez déjà votre base `Achats_données.accdb`. Pas de manipulation à faire.

### Étape 2 — Lancer l'app
1. Double-cliquez sur **`MultirexDMS_Updater.exe`**
2. Une fenêtre s'ouvre

### Étape 3 — Choisir le fichier
- Cliquez sur **📁 Parcourir...**
- Sélectionnez votre `Achats_données.accdb`

### Étape 4 — Aperçu (sécurité)
- Cliquez sur **🔍 Aperçu (sans modifier)**
- L'app analyse votre fichier et **vous montre ce qui va changer** :
  - X nouvelles lignes
  - Y lignes modifiées
  - Z erreurs éventuelles (doublons, incohérences)
- ⚠️ **Aucune modification n'est faite à ce stade.** Vous pouvez fermer l'app si quelque chose vous déplaît.

### Étape 5 — Confirmer
Si l'aperçu vous va, cliquez sur **✅ Confirmer et mettre à jour Supabase**.
- L'app pousse les changements
- Une barre de progression s'affiche
- Quand c'est fini, vous voyez un message de succès

### Étape 6 — Vérifier sur le site
Ouvrez https://dms-frontend-phi-six.vercel.app — vos nouvelles données sont visibles immédiatement.

---

## Garanties techniques

- ✅ **Aucun doublon possible** : chaque ligne est identifiée par sa clé unique (n_moteur, n_bv, etc.). Si une ligne existe déjà, elle est mise à jour, pas dupliquée.
- ✅ **Mise à jour incrémentale** : seules les lignes nouvelles ou modifiées depuis le dernier import sont touchées. Vos données existantes ne sont pas écrasées sans raison.
- ✅ **Aperçu obligatoire avant écriture** : impossible de "casser" la base par erreur — vous voyez toujours ce qui va changer avant de valider.
- ✅ **Journal complet** : chaque opération est tracée dans la table `import_log` Supabase. En cas de doute, on peut auditer.
- ✅ **Pas d'accès à votre PC** : votre fichier `.accdb` ne quitte pas votre machine, sauf vers Supabase via une connexion chiffrée.

---

## En cas de problème

1. **Le bouton "Aperçu" affiche une erreur** → noter le message du journal et le transmettre à l'équipe technique.
2. **L'aperçu donne des chiffres bizarres** → ne pas cliquer "Confirmer", contacter l'équipe.
3. **Le site web n'affiche pas les nouvelles données après import** → vérifier la requête SQL côté Supabase ou rafraîchir le navigateur (Ctrl+F5).

---

## FAQ

**Q : À quelle fréquence dois-je faire une mise à jour ?**
R : Aussi souvent que vous voulez. Idéalement après chaque session de saisie Access (en fin de journée ou semaine).

**Q : Si je lance l'app 2 fois de suite, ça crée des doublons ?**
R : Non. La 2e exécution détecte que toutes les lignes existent déjà et ne fait rien (ou seulement les éventuels nouveaux ajouts).

**Q : Et si plusieurs personnes modifient la base Access en même temps ?**
R : L'app prend la version au moment de l'import. Si quelqu'un modifie après, il faudra re-importer plus tard.

**Q : Combien de temps prend une mise à jour ?**
R : Environ 1 à 3 minutes pour 7 000 nouvelles lignes (soit ~3 mois d'activité).
