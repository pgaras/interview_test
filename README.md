# Interview Test README
This is the README file for Interview Test Project: A CRUD application using Django REST Framework and AngularJS.

## How to Run
In order to run this package, do the following steps:

1. Assuming that you have a server already setup, simply clone this project's repository to your desired project 
diretory. Make sure that your server already has python 2.7 or greater and pip installed.
2. Install the project dependencies by running:

        pip install -r requirements.txt

3. There's no need to do migration tasks from manage.py as the database file used by this project (db.sqlite3) already 
reflects the current database migrations. The database file also contains a few entries for Library and Project models.
4. If you wish to use a bare database with no library and project entries, go to config/settings.py and change this 
setting from:

    ```
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    ```
    
    to:

    ```
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3.base'),
            }
        }
    ```    

5. From your terminal, you may now run:

        python manage.py runserver 0.0.0.0:8000
    
    This will run your Project app at port 8000. Try to access the Project app from your browser:
   
        http://< your server ip >:8000
   
   You should now be able to access Projects! The UI should be straightforward.
   
6. You can try to log in using these accounts and compare library and project permissions:

| Username | Account Type | With Project Privileges | Password |
|----------|:------------:|:----:|:------|
| admin    |  admin | NO | testing123 |
| adminuser | admin | YES |  testing123 |
| adminsuperuser | superuser | - | testing123 |
| user1    |  user | YES | testing123 |
| user2 | user | NO |  testing123 |

Note: admin accounts have Library Privileges activated by default. Users with Project Privileges should have a group 
permission of 'project access' with all user permissions granted for api/projects. You can verify this by using the 
<i>adminsuperuser</i> account at the admin site below:

    http://< your server ip >:8000/admin/

## API Documentation
The API Documentation uses DRF's built-in browsable API. It should be located at:

    http://< your server ip >:8000/api/

## UI Improvements
While it might be out of scope, some UI features I have incorporated to this project are the following:

* Bootstrap's responsive output (should work with both mobile and desktop browsers)

* Cancel button - I have to implement this as it has been my practice to always include this feature. Also, it helps 
me when I do the data entry work and interface tests.
      
* Alert notification - another feature from Bootstrap - at least I would know if my methods worked or not.

* Highlighted Active Library Items

## What can be improved about this project?
The task flow is generally clear and concise, although I only came to know of the API Documentation requirement
when I opened the original README file. Previously, I only used views for processing the AJAX requests and the
documentation would have been easier included in the viewsets. It is for this reason that I have to convert my views
to viewsets to satisfy the documentation requirement without additional hassle.

## What would you do next?
Additional features that would be considered are the following:

* constraint checks (see below)
* unit and functional tests
* messaging queue that can do a lot of stuff, like notifying users who are concurrently logged in on data changes, or 
using it in tandem with Django's caching to update data only when changes have been detected, thereby reducing database 
hits.
* creation of NPM or Bower manifest.json for deployment to dispel the need of committing third-party static js/css 
assets
* api endpoints for integrating with scheduling software applications for start and end of active dates
* other useful features that require API integrations such as build status, online avalability checks, and package 
update notices
 
## What parts didn't you implement?
Constraint checks on dates:
* checking 'active_end_date' from projects with libraries whose 'active_start_date' fields have a later date (greater 
value)

Constraint checks on duplicate library entries:
* You can enter the same library with the same version multiple times in a single project.

Using DRF's detail routing for PUT and DELETE Ajax calls
* Due to lack of time and still struggling to understand how to use $resource in factories, I just added the AJAX calls 
to the controllers directly by using $http instead and ditching the id as part of the Ajax URL

Works on DEBUG = True setting only
* No effort was made to make the project run with DEBUG = False. Also no CSRF
test checks were made
