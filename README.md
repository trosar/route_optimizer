# route_optimizer

This is a route optimizer application developed for the Scouting America Troop 60 Washington scouts. It is used to determine the best route to pickup Christmas Trees that need to be recycled. 

## Installation (On Mac)
```
brew install gh
brew install orbstack
```

## Project Structure
* static/

  Folder contains the images/static files used by the website. 
  See how the index.html file below uses the logo png file to 
  get an idea how to use files in the the static folder.

* templates/

  Folder contains the HTML files used by the website
  index.html is the main page that is served to the users by the Flask app
* app.py

  The main Flask application. It has a single route. 
  If method is GET (intital reqquest to the page), 
    it shows the index.html file to the user.
  If method is POST (when form is submitted),
    it runs the algorithm and returns the formatted data.

* Dockerfile

  Contains the complete application's docker image environment and startup commands

* env_vars.env

  Contains the environment variables that are used by the application. 
  Please update them before running the application. 
  DO NOT commit these variables to Git by mistake as everyone will be able to see these values.

## Project Build (on local machine)
* Assuming you have started Orbstack locally (see installation above)
* Update the code files
* Update the Dockerfile (if required)
* Run the below command in the root folder
```
  sh 01_deploy_local_app.sh
```

## Save built Docker Image on DockerHub
* Run the below command in the root folder
```
  sh 02_save_docker_image.sh
```

## Deploy code to GitHub / Railway
* Run the below command in the root folder
```
  sh 03_deploy_app.sh
```
