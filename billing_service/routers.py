class AuthRouter:
    """
    Database router to direct auth and session models to the shared auth_db.
    This router ensures that:
    - Auth models are READ from the shared database
    - Auth models are NEVER migrated to the shared database (main backend handles that)
    """
    
    def db_for_read(self, model, **hints):
        """Direct reads of auth models to auth_db"""
        if model._meta.app_label in ['auth', 'sessions', 'contenttypes']:
            return 'auth_db'
        return 'default'

    def db_for_write(self, model, **hints):
        """Direct writes of auth models to auth_db"""
        if model._meta.app_label in ['auth', 'sessions', 'contenttypes']:
            return 'auth_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between auth models and billing models"""
        auth_models = ['auth', 'sessions', 'contenttypes']
        if obj1._meta.app_label in auth_models or obj2._meta.app_label in auth_models:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        CRITICAL: Prevent migrations on auth_db!
        Only the main backend should migrate auth tables.
        """
        if app_label in ['auth', 'sessions', 'contenttypes', 'admin']:
            # Never migrate these to auth_db - main backend handles it
            return db == 'default'
        # All other apps only migrate to default
        return db == 'default'
