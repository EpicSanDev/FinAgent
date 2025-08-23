# Guide de Test d'Accessibilité - FinAgent

## Vue d'ensemble

Ce guide détaille les procédures de test pour valider la conformité WCAG 2.1 AA de l'interface FinAgent. Les tests couvrent tous les aspects de l'accessibilité implémentés.

## Outils de Test Recommandés

### Outils Automatisés
- **axe DevTools** - Extension Chrome/Firefox pour tests automatisés
- **WAVE** - Évaluateur d'accessibilité web
- **Lighthouse** - Audit d'accessibilité intégré à Chrome
- **Pa11y** - Outil en ligne de commande pour tests automatisés

### Lecteurs d'Écran
- **NVDA** (Windows) - Gratuit et largement utilisé
- **JAWS** (Windows) - Standard professionnel
- **VoiceOver** (macOS) - Intégré au système
- **Orca** (Linux) - Lecteur d'écran open source

### Tests Clavier
- Navigation sans souris
- Tests avec différents navigateurs
- Validation des raccourcis clavier

## Tests de Navigation Clavier

### 1. Navigation Générale
```
✓ Tab - Navigation séquentielle vers l'avant
✓ Shift+Tab - Navigation séquentielle vers l'arrière
✓ Flèches - Navigation dans les groupes de contrôles
✓ Espace - Activation des boutons et checkboxes
✓ Entrée - Activation des liens et boutons
✓ Échap - Fermeture des modales et menus
```

### 2. Skip Links
```
Test: Appuyer sur Tab dès le chargement de la page
✓ Le premier élément focusé doit être "Aller au contenu principal"
✓ Activation avec Entrée doit déplacer le focus vers #main-content
✓ Le skip link doit être visible au focus
```

### 3. Navigation dans les Widgets
```
Test: Naviguer dans le widget "Résumé du Portefeuille"
✓ Tab pour entrer dans le widget
✓ Flèches pour naviguer entre les métriques
✓ Les valeurs doivent être annoncées correctement
✓ Les changements (hausse/baisse) doivent être vocalisés
```

### 4. Navigation dans les Tableaux
```
Test: Tableaux de données de marché
✓ Flèches pour naviguer entre les cellules
✓ Ctrl+Flèches pour naviguer par section
✓ Home/End pour aller au début/fin de ligne
✓ Page Up/Down pour navigation rapide
```

### 5. Raccourcis Clavier Globaux
```
✓ Alt+1 - Dashboard
✓ Alt+2 - Portefeuille
✓ Alt+3 - Marché
✓ Alt+4 - Trading
✓ Alt+H - Aller au contenu principal
✓ Alt+S - Focus sur la recherche
✓ Alt+N - Ouvrir les notifications
```

## Tests de Lecteur d'Écran

### 1. Structure et Landmarks
```
Test avec NVDA/VoiceOver:
✓ Landmarks détectés (banner, navigation, main, complementary)
✓ Hiérarchie des titres (H1 > H2 > H3) correcte
✓ Régions étiquetées de manière appropriée
✓ Boutons et liens ont des labels descriptifs
```

### 2. Contenu Dynamique
```
Test: Changements de données en temps réel
✓ Régions live annoncent les mises à jour
✓ Changements de prix vocalisés automatiquement
✓ Nouvelles notifications annoncées
✓ Messages d'erreur lus immédiatement
```

### 3. Formulaires
```
Test: Formulaires de trading et authentification
✓ Labels associés aux champs
✓ Instructions et erreurs annoncées
✓ Groupes de champs identifiés
✓ Champs requis indiqués clairement
```

### 4. Graphiques et Visualisations
```
Test: Graphiques financiers
✓ Description textuelle disponible
✓ Données tabulaires alternatives fournies
✓ Tendances décrites en texte
✓ Points de données accessibles au clavier
```

## Tests de Contraste et Visibilité

### 1. Contraste des Couleurs
```
Test avec outils de contraste:
✓ Texte normal: ratio ≥ 4.5:1
✓ Texte large: ratio ≥ 3:1
✓ Éléments d'interface: ratio ≥ 3:1
✓ Mode sombre: mêmes exigences respectées
```

### 2. Indicateurs Visuels
```
Test: Focus et états visuels
✓ Focus visible sur tous les éléments interactifs
✓ États hover et active clairement distinguables
✓ Indicateurs d'état (erreur, succès) visibles
✓ Pas de dépendance uniquement à la couleur
```

### 3. Mode Contraste Élevé
```
Test: Activation du mode contraste élevé
✓ Bouton d'activation accessible
✓ Tous les éléments restent visibles
✓ Texte reste lisible
✓ Bordures et séparateurs visibles
```

## Tests de Réactivité et Zoom

### 1. Zoom jusqu'à 200%
```
Test: Agrandissement de la page
✓ Contenu reste lisible et fonctionnel
✓ Pas de défilement horizontal
✓ Boutons et liens restent cliquables
✓ Informations importantes visibles
```

### 2. Appareils Mobiles
```
Test: Navigation tactile accessible
✓ Cibles tactiles ≥ 44px
✓ Espacement suffisant entre éléments
✓ Gestes alternatifs disponibles
✓ Navigation clavier fonctionnelle sur mobile
```

## Tests de Préférences Utilisateur

### 1. Réduction du Mouvement
```
Test: Paramètre "Réduire les animations"
✓ Animations désactivées ou réduites
✓ Transitions simplifiées
✓ Mouvement automatique stoppé
✓ Alternative statique disponible
```

### 2. Préférences de Taille de Police
```
Test: Paramètre "Texte large"
✓ Taille de police augmentée
✓ Espacement ajusté automatiquement
✓ Lisibilité maintenue
✓ Interface reste fonctionnelle
```

## Tests de Performance d'Accessibilité

### 1. Temps de Réponse
```
Test: Rapidité des annonces
✓ Feedback immédiat pour les actions
✓ Annonces live sans délai excessif
✓ Navigation clavier fluide
✓ Pas de blocage du focus
```

### 2. Efficacité de Navigation
```
Test: Parcours utilisateur accessible
✓ Nombre minimal de tabs pour atteindre le contenu
✓ Groupement logique des éléments
✓ Skip links efficaces
✓ Raccourcis clavier utiles
```

## Checklist de Validation WCAG 2.1 AA

### Niveau A
- [ ] 1.1.1 Contenu non textuel
- [ ] 1.2.1 Contenu audio et vidéo pré-enregistré
- [ ] 1.2.2 Sous-titres (pré-enregistrés)
- [ ] 1.2.3 Audio-description ou version de remplacement
- [ ] 1.3.1 Information et relations
- [ ] 1.3.2 Ordre séquentiel logique
- [ ] 1.3.3 Caractéristiques sensorielles
- [ ] 1.4.1 Utilisation de la couleur
- [ ] 1.4.2 Contrôle du son
- [ ] 2.1.1 Clavier
- [ ] 2.1.2 Pas de piège au clavier
- [ ] 2.1.4 Raccourcis clavier
- [ ] 2.2.1 Réglage du délai
- [ ] 2.2.2 Mettre en pause, arrêter, masquer
- [ ] 2.3.1 Pas plus de trois flashs
- [ ] 2.4.1 Contourner les blocs
- [ ] 2.4.2 Titre de page
- [ ] 2.4.3 Parcours du focus
- [ ] 2.4.4 Fonction du lien (selon le contexte)
- [ ] 2.5.1 Gestes pour les pointeurs
- [ ] 2.5.2 Annulation du pointeur
- [ ] 2.5.3 Étiquette dans le nom
- [ ] 2.5.4 Activation par le mouvement
- [ ] 3.1.1 Langue de la page
- [ ] 3.2.1 Au focus
- [ ] 3.2.2 À la saisie
- [ ] 3.3.1 Identification des erreurs
- [ ] 3.3.2 Étiquettes ou instructions
- [ ] 4.1.1 Analyse syntaxique
- [ ] 4.1.2 Nom, rôle et valeur

### Niveau AA
- [ ] 1.2.4 Sous-titres (en direct)
- [ ] 1.2.5 Audio-description (pré-enregistré)
- [ ] 1.3.4 Orientation
- [ ] 1.3.5 Identifier la finalité de la saisie
- [ ] 1.4.3 Contraste (minimum)
- [ ] 1.4.4 Redimensionnement du texte
- [ ] 1.4.5 Texte sous forme d'image
- [ ] 1.4.10 Redistribution
- [ ] 1.4.11 Contraste du contenu non textuel
- [ ] 1.4.12 Espacement du texte
- [ ] 1.4.13 Contenu au survol ou au focus
- [ ] 2.4.5 Plusieurs façons
- [ ] 2.4.6 En-têtes et étiquettes
- [ ] 2.4.7 Focus visible
- [ ] 3.1.2 Langue d'un passage
- [ ] 3.2.3 Navigation cohérente
- [ ] 3.2.4 Identification cohérente
- [ ] 3.3.3 Suggestion après une erreur
- [ ] 3.3.4 Prévention des erreurs (juridiques, financières, de données)
- [ ] 4.1.3 Messages de statut

## Scripts de Test Automatisés

### Test axe-core
```javascript
// Test d'accessibilité automatisé avec axe-core
async function runAccessibilityTests() {
    const results = await axe.run();
    
    if (results.violations.length > 0) {
        console.error('Violations d\'accessibilité trouvées:', results.violations);
        return false;
    }
    
    console.log('Tests d\'accessibilité réussis!');
    return true;
}
```

### Test de Navigation Clavier
```javascript
// Test automatisé de navigation clavier
function testKeyboardNavigation() {
    const focusableElements = document.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    let success = true;
    
    focusableElements.forEach((element, index) => {
        element.focus();
        
        if (document.activeElement !== element) {
            console.error(`Élément non focusable: ${element.tagName}#${element.id}`);
            success = false;
        }
        
        // Vérifier le focus visible
        const styles = getComputedStyle(element, ':focus');
        if (!styles.outline && !styles.boxShadow) {
            console.warn(`Focus non visible: ${element.tagName}#${element.id}`);
        }
    });
    
    return success;
}
```

## Rapport de Test Type

### Template de Rapport
```
# Rapport de Test d'Accessibilité - FinAgent
Date: [DATE]
Testeur: [NOM]
Navigateur: [NAVIGATEUR + VERSION]
Lecteur d'écran: [LECTEUR + VERSION]

## Résumé Exécutif
- Conformité WCAG 2.1 AA: [OUI/NON/PARTIELLE]
- Violations critiques: [NOMBRE]
- Violations mineures: [NOMBRE]
- Score global: [X/10]

## Tests Réussis
- [Liste des tests passés avec succès]

## Problèmes Identifiés
### Critique
- [Problème 1]: [Description] - [Impact] - [Solution recommandée]

### Mineur
- [Problème 2]: [Description] - [Impact] - [Solution recommandée]

## Recommandations
1. [Recommandation prioritaire 1]
2. [Recommandation prioritaire 2]
3. [Améliorations suggérées]

## Validation Finale
- [ ] Tests automatisés passés
- [ ] Tests manuels validés
- [ ] Tests utilisateur réels effectués
- [ ] Documentation mise à jour
```

Ce guide de test complet permet de valider rigoureusement toutes les fonctionnalités d'accessibilité implémentées dans FinAgent et d'assurer la conformité WCAG 2.1 AA.