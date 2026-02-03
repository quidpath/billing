class AuthRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "auth" or model._meta.app_label == "sessions":
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
