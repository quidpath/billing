class AuthRouter:
    """
    A router to control database operations for authentication models.
    Routes auth, admin, contenttypes, and sessions to the shared auth_db.
    All other models go to the default database.
    """
    auth_apps = {'auth', 'admin', 'contenttypes', 'sessions'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and admin models go to auth_db.
        """
        if model._meta.app_label in self.auth_apps:
            return 'auth_db'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and admin models go to auth_db.
        """
        if model._meta.app_label in self.auth_apps:
            return 'auth_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in the same database.
        """
        db_set = {'auth_db', 'default'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure auth apps only appear in the 'auth_db' database.
        """
        if app_label in self.auth_apps:
            return db == 'auth_db'
        return db == 'default'