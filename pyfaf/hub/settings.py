# -*- coding: utf-8 -*-
# Django settings for hub (kobo hub) project.
import os
import kobo
import pyfaf.config

# Definition of PROJECT_DIR, just for convenience:
# you can use it instead of specifying the full path
PROJECT_DIR = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

def db_engine():
    if pyfaf.config.CONFIG["cache.dbtype"] == "sqlite3":
        return 'django.db.backends.sqlite3'
    elif pyfaf.config.CONFIG["cache.dbtype"] == "mysql":
        return 'django.db.backends.mysql'

    return 'django.db.backends.sqlite3'

def db_name():
    if pyfaf.config.CONFIG["cache.dbtype"] == "sqlite3":
        return os.path.join(pyfaf.config.CONFIG["cache.directory"], "sqlite.db")
    elif pyfaf.config.CONFIG["cache.dbtype"] == "mysql":
        return pyfaf.config.CONFIG["cache.mysqldb"]

    return os.path.join(pyfaf.config.CONFIG["cache.directory"], "sqlite.db")

DATABASES = {
    'default': {
        # 'django.db.backends.' + {'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'}
        'ENGINE': db_engine(),
        # Or path to database file if using sqlite3.
        'NAME': db_name(),
        # Not used with sqlite3.
        'USER': pyfaf.config.CONFIG["cache.mysqluser"],
        # Not used with sqlite3.
        'PASSWORD': pyfaf.config.CONFIG["cache.mysqlpasswd"],
        # Set to empty string for localhost. Not used with sqlite3.
        'HOST': pyfaf.config.CONFIG["cache.mysqlhost"],
        # Set to empty string for default. Not used with sqlite3.
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Prague'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to task logs and other files
FILES_PATH = '/var/spool/faf/hub'

# Files for kobo tasks with predefined structure
TASK_DIR = os.path.join(FILES_PATH, 'tasks')

# Root directory for uploaded files
UPLOAD_DIR = os.path.join(FILES_PATH, 'upload')

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, "media/")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/faf/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/faf/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = "@RANDOM_STRING@"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
#        'django.template.loaders.eggs.Loader',
    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Krb5AuthenticationMiddleware must be loaded *after* AuthenticationMiddleware
    #'kobo.django.auth.krb5.Krb5AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # kobo related middleware:
    'kobo.hub.middleware.WorkerMiddleware',
    'kobo.django.menu.middleware.MenuMiddleware',
)

ROOT_URLCONF = 'pyfaf.hub.urls'
ROOT_MENUCONF = 'pyfaf.hub.menu'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'kobo.django.menu.context_processors.menu_context_processor',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, "templates"),
    os.path.join(os.path.dirname(kobo.__file__), "hub", "templates"),
)

INSTALLED_APPS = (
    'kobo.django.auth',   # load this app first to make sure the username length hack is applied first
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # kobo apps:
    'kobo.django.upload',
    'kobo.hub',
    # add your apps here:
)

# kobo XML-RPC API calls
# If you define additional methods, you have to list them there.
XMLRPC_METHODS = {
    # 'handler':
    'client': (
        # module with rpc methods     prefix which is added to all methods from the module
        ('kobo.hub.xmlrpc.auth',      'auth'),
        ('kobo.hub.xmlrpc.client',    'client'),
        ('kobo.hub.xmlrpc.system',    'system'),
        ('kobo.django.upload.xmlrpc', 'upload'),
    ),
    'worker': (
        ('kobo.hub.xmlrpc.auth',      'auth'),
        ('kobo.hub.xmlrpc.system',    'system'),
        ('kobo.hub.xmlrpc.worker',    'worker'),
        ('kobo.django.upload.xmlrpc', 'upload'),
    ),
}

# override default values with custom ones from local settings
try:
    from pyfaf.hub.settings_local import *
except ImportError:
    pass
