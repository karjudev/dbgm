# Database della Giurisprudenza di Merito

This is the source code for the automatic anonymization platform and data visualization tool currently hosted by the University of Pisa at its [Official Link](http://dbgm.unipi.it).

## Running the code

You have to create a file called `.env`, with the same field as the `.env.example` file you find in this repository.

Then simply run the following command:
```bash
$ docker compose up --build
```

## Development

To modify a single sub-service, head to its subdirectory (i.e. `./streamlit`) and create a virtual environment with your favourite tool. Then install the required libraries as follows:
```bash
$ python -r requirements.txt
```