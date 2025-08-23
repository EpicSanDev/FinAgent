"""
Utilitaires de progression pour la CLI FinAgent.

Ce module fournit des barres de progression, spinners et
indicateurs de statut pour les opérations longues.
"""

import time
import asyncio
from typing import Any, Callable, Optional, Union, List, Dict
from contextlib import contextmanager
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.progress import (
    Progress, 
    BarColumn, 
    TextColumn, 
    TimeRemainingColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
    SpinnerColumn,
    TaskID
)
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout

console = Console()


class ProgressManager:
    """Gestionnaire centralisé des barres de progression."""
    
    def __init__(self):
        self.active_progress: Optional[Progress] = None
        self.active_tasks: Dict[str, TaskID] = {}
    
    def create_progress(self, 
                       description: str = "Progression",
                       show_percentage: bool = True,
                       show_time_remaining: bool = True,
                       show_time_elapsed: bool = False,
                       show_speed: bool = False) -> Progress:
        """
        Crée une nouvelle barre de progression.
        
        Args:
            description: Description de la tâche
            show_percentage: Afficher le pourcentage
            show_time_remaining: Afficher le temps restant
            show_time_elapsed: Afficher le temps écoulé
            show_speed: Afficher la vitesse
            
        Returns:
            Instance de Progress configurée
        """
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
        ]
        
        if show_percentage:
            columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))
        
        if show_time_remaining:
            columns.append(TimeRemainingColumn())
        
        if show_time_elapsed:
            columns.append(TimeElapsedColumn())
        
        if show_speed:
            columns.append(TextColumn("[progress.data.speed]{task.fields[speed]}"))
        
        progress = Progress(*columns, console=console, refresh_per_second=10)
        self.active_progress = progress
        
        return progress
    
    def add_task(self, 
                description: str,
                total: Optional[int] = None,
                **kwargs) -> TaskID:
        """
        Ajoute une tâche à la progression active.
        
        Args:
            description: Description de la tâche
            total: Nombre total d'étapes
            **kwargs: Arguments supplémentaires
            
        Returns:
            ID de la tâche
        """
        if not self.active_progress:
            self.active_progress = self.create_progress()
        
        task_id = self.active_progress.add_task(description, total=total, **kwargs)
        self.active_tasks[description] = task_id
        
        return task_id
    
    def update_task(self, 
                   task_id: Union[TaskID, str],
                   advance: Optional[int] = None,
                   completed: Optional[int] = None,
                   description: Optional[str] = None,
                   **kwargs) -> None:
        """
        Met à jour une tâche.
        
        Args:
            task_id: ID de la tâche ou description
            advance: Nombre d'étapes à avancer
            completed: Nombre total d'étapes complétées
            description: Nouvelle description
            **kwargs: Arguments supplémentaires
        """
        if not self.active_progress:
            return
        
        # Résolution de l'ID si c'est une description
        if isinstance(task_id, str):
            task_id = self.active_tasks.get(task_id)
            if task_id is None:
                return
        
        self.active_progress.update(
            task_id,
            advance=advance,
            completed=completed,
            description=description,
            **kwargs
        )
    
    def complete_task(self, task_id: Union[TaskID, str]) -> None:
        """
        Marque une tâche comme complétée.
        
        Args:
            task_id: ID de la tâche ou description
        """
        if isinstance(task_id, str):
            task_id = self.active_tasks.get(task_id)
            if task_id is None:
                return
        
        if self.active_progress:
            # Récupération du total pour compléter
            task = self.active_progress.tasks[task_id]
            if task.total:
                self.active_progress.update(task_id, completed=task.total)
    
    @contextmanager
    def progress_context(self):
        """Context manager pour la gestion automatique des barres de progression."""
        if not self.active_progress:
            self.active_progress = self.create_progress()
        
        with self.active_progress:
            try:
                yield self.active_progress
            finally:
                self.active_progress = None
                self.active_tasks.clear()


class SpinnerManager:
    """Gestionnaire de spinners pour les opérations indéterminées."""
    
    def __init__(self):
        self.active_spinner: Optional[Live] = None
        self.spinner_thread: Optional[Thread] = None
        self.stop_event: Optional[Event] = None
    
    def start_spinner(self, 
                     text: str,
                     spinner_type: str = "dots") -> None:
        """
        Démarre un spinner.
        
        Args:
            text: Texte à afficher
            spinner_type: Type de spinner (dots, arc, etc.)
        """
        if self.active_spinner:
            self.stop_spinner()
        
        spinner = Spinner(spinner_type)
        spinner_text = Text.assemble(
            (f"{spinner} ", "blue"),
            (text, "white")
        )
        
        self.active_spinner = Live(spinner_text, console=console, refresh_per_second=10)
        self.active_spinner.start()
    
    def update_spinner(self, text: str) -> None:
        """
        Met à jour le texte du spinner.
        
        Args:
            text: Nouveau texte
        """
        if self.active_spinner:
            spinner_text = Text.assemble(
                ("⠿ ", "blue"),  # Caractère de spinner fixe pour la mise à jour
                (text, "white")
            )
            self.active_spinner.update(spinner_text)
    
    def stop_spinner(self) -> None:
        """Arrête le spinner actif."""
        if self.active_spinner:
            self.active_spinner.stop()
            self.active_spinner = None
    
    @contextmanager
    def spinner_context(self, text: str, spinner_type: str = "dots"):
        """Context manager pour les spinners."""
        self.start_spinner(text, spinner_type)
        try:
            yield self
        finally:
            self.stop_spinner()


class StepProgress:
    """Progression par étapes avec descriptions détaillées."""
    
    def __init__(self, steps: List[str], title: str = "Progression"):
        self.steps = steps
        self.title = title
        self.current_step = 0
        self.total_steps = len(steps)
        self.start_time = time.time()
        self.step_times: List[float] = []
    
    def next_step(self, message: Optional[str] = None) -> None:
        """
        Passe à l'étape suivante.
        
        Args:
            message: Message optionnel pour cette étape
        """
        if self.current_step < self.total_steps:
            step_time = time.time()
            self.step_times.append(step_time)
            
            step_desc = self.steps[self.current_step]
            if message:
                step_desc += f" - {message}"
            
            # Calcul du temps estimé
            if self.current_step > 0:
                avg_time_per_step = (step_time - self.start_time) / self.current_step
                remaining_steps = self.total_steps - self.current_step
                eta = remaining_steps * avg_time_per_step
                eta_text = f" (ETA: {eta:.1f}s)"
            else:
                eta_text = ""
            
            progress_text = (
                f"[{self.current_step + 1}/{self.total_steps}] "
                f"{step_desc}{eta_text}"
            )
            
            console.print(f"🔄 {progress_text}", style="blue")
            self.current_step += 1
    
    def complete(self, message: str = "Terminé") -> None:
        """
        Marque la progression comme complétée.
        
        Args:
            message: Message de fin
        """
        total_time = time.time() - self.start_time
        console.print(
            f"✅ {message} (durée totale: {total_time:.2f}s)",
            style="green bold"
        )
    
    def error(self, message: str) -> None:
        """
        Marque la progression comme échouée.
        
        Args:
            message: Message d'erreur
        """
        console.print(f"❌ Erreur: {message}", style="red bold")


def with_progress(description: str = "Traitement en cours..."):
    """
    Décorateur pour ajouter automatiquement une barre de progression.
    
    Args:
        description: Description de la tâche
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            progress_manager = ProgressManager()
            
            with progress_manager.progress_context() as progress:
                task_id = progress.add_task(description, total=None)
                
                try:
                    result = func(*args, **kwargs)
                    progress.update(task_id, description=f"{description} ✅")
                    return result
                except Exception as e:
                    progress.update(task_id, description=f"{description} ❌")
                    raise
        
        return wrapper
    return decorator


def with_spinner(text: str = "Traitement..."):
    """
    Décorateur pour ajouter automatiquement un spinner.
    
    Args:
        text: Texte à afficher
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            spinner_manager = SpinnerManager()
            
            with spinner_manager.spinner_context(text):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class BatchProgress:
    """Gestionnaire pour le traitement par lots avec progression."""
    
    def __init__(self, 
                 items: List[Any],
                 batch_size: int = 10,
                 description: str = "Traitement par lots"):
        self.items = items
        self.batch_size = batch_size
        self.description = description
        self.total_items = len(items)
        self.processed_items = 0
        self.progress_manager = ProgressManager()
    
    def process_batches(self, 
                       processor_func: Callable[[List[Any]], Any],
                       show_individual_progress: bool = True) -> List[Any]:
        """
        Traite les éléments par lots avec progression.
        
        Args:
            processor_func: Fonction pour traiter un lot
            show_individual_progress: Afficher la progression de chaque lot
            
        Returns:
            Liste des résultats
        """
        results = []
        
        with self.progress_manager.progress_context() as progress:
            main_task = progress.add_task(
                self.description,
                total=self.total_items
            )
            
            # Traitement par lots
            for i in range(0, self.total_items, self.batch_size):
                batch = self.items[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (self.total_items + self.batch_size - 1) // self.batch_size
                
                if show_individual_progress:
                    batch_task = progress.add_task(
                        f"Lot {batch_num}/{total_batches}",
                        total=len(batch)
                    )
                
                # Traitement du lot
                try:
                    batch_result = processor_func(batch)
                    results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                    
                    # Mise à jour de la progression
                    self.processed_items += len(batch)
                    progress.update(main_task, completed=self.processed_items)
                    
                    if show_individual_progress:
                        progress.update(batch_task, completed=len(batch))
                        progress.remove_task(batch_task)
                    
                except Exception as e:
                    progress.update(
                        main_task,
                        description=f"{self.description} ❌ Erreur au lot {batch_num}"
                    )
                    raise
                
                # Petite pause pour éviter la surcharge
                time.sleep(0.1)
            
            progress.update(main_task, description=f"{self.description} ✅")
        
        return results


async def async_progress_wrapper(async_func: Callable, 
                               description: str = "Traitement asynchrone...") -> Any:
    """
    Wrapper pour ajouter une progression aux fonctions asynchrones.
    
    Args:
        async_func: Fonction asynchrone à wrapper
        description: Description de la tâche
        
    Returns:
        Résultat de la fonction
    """
    progress_manager = ProgressManager()
    
    with progress_manager.progress_context() as progress:
        task_id = progress.add_task(description, total=None)
        
        try:
            result = await async_func()
            progress.update(task_id, description=f"{description} ✅")
            return result
        except Exception as e:
            progress.update(task_id, description=f"{description} ❌")
            raise


def create_status_panel(title: str, 
                       status_items: Dict[str, str],
                       style: str = "blue") -> Panel:
    """
    Crée un panel de statut avec plusieurs éléments.
    
    Args:
        title: Titre du panel
        status_items: Dictionnaire des éléments de statut
        style: Style du panel
        
    Returns:
        Panel formaté
    """
    content_lines = []
    
    for label, status in status_items.items():
        # Détermination de l'emoji selon le statut
        if "✅" in status or "terminé" in status.lower():
            emoji = "✅"
        elif "❌" in status or "erreur" in status.lower():
            emoji = "❌"
        elif "⏳" in status or "en cours" in status.lower():
            emoji = "⏳"
        else:
            emoji = "ℹ️"
        
        content_lines.append(f"{emoji} {label}: {status}")
    
    content = "\n".join(content_lines)
    
    return Panel(
        content,
        title=title,
        border_style=style
    )


# Instances globales réutilisables
progress_manager = ProgressManager()
spinner_manager = SpinnerManager()