---
title: Tennis Api
emoji: ⚡
colorFrom: purple
colorTo: yellow
sdk: docker
pinned: false
short_description: API for training and interacting with tennis-insights models
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# tennis-api

## Docker Install  

To get the service for training the model and giving predictions up and running locally, simply follow the steps hereafter:

### Build the API image

From the root of the project:  
```bash
$> docker build . -t tennis_api:latest -f Dockerfile
```  

### Run it

From the root of the project:  
```bash
$> docker run --rm -p 7860:7860 --mount type=bind,src=./.env,target=/app/.env tennis_api:latest
```  

Then go to [http://localhost:7860/](http://localhost:7860/)

The API should be accessible:  
![exposed API methods](api.png)  

## Resources  

Website: [http://www.tennis-data.co.uk/alldata.php](http://www.tennis-data.co.uk/alldata.php)  

## License  

©2025