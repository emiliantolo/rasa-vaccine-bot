# rasa-vaccine-bot

## Description

__Conversational agent with Rasa and Alexa__ project

Language Understanding Systems course, University of Trento, 2021

## Prerequisites

The project was tested in virtual environment on Windows 10 using Python 3.7.0, with Rasa 2.7.1 and CUDA 10.1

## Usage

### Clone and run
```code
git clone git@github.com:emiliantolo/rasa-vaccine-bot.git
cd rasa-vaccine-bot
```
### Generate NLU with chatette
```code
.\chatette\gen.bat
```
### Train model
```code
rasa train
```
### Run
#### Run duckling server
```code
docker run -p 8000:8000 rasa/duckling
```
#### Run actions server
```code
rasa run actions
```
#### Run rasa shell
```code
rasa shell
```

## Author

Emiliano Tolotti emiliano.tolotti@studenti.unitn.it
