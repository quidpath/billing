class AuthRouter:
    """
    Database router to direct auth and session models to the shared auth_db.
    This router ensures that:
    - Auth models are READ from the shared database
    - Auth models are NEVER migrated to the shared database (main backend handles that)
    """
    
    def db_for_read(self, model, **hints):
        """Direct reads of auth models to auth_db"""
        if model._meta.app_label in ["auth", "sessions", 'contenttypes']:
            return "auth_db"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "auth" or model._meta.app_label == "sessions":
            return "auth_db"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == "auth" or obj2._meta.app_label == "auth":
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "auth" or app_label == "sessions":
            return db == "auth_db"
        return db == "default"
