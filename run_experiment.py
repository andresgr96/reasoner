import os
import argparse
from reasoner_class import Reasoner
from colorama import Fore, Style
from os.path import exists, basename
import pandas as pd

if __name__ == "__main__":
    results_folder = "./results"

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    pizza_ont_and_class = ["./ontologies/pizza.owl", "Margherita"]
    food_ont_and_class = ["./ontologies/food.owl.xml", "FOODON_03460238"]
    skin_ont_and_class = ["./ontologies/skin.owl", "Integrin"]
    clinical_ont_and_class = ["./ontologies/clinical.owl.xml", "Amyloidosis"]
    donut_ont_and_class = ["./ontologies/donut_store.owl", "FilledDonut"]

    ontologies = [pizza_ont_and_class, food_ont_and_class, skin_ont_and_class, clinical_ont_and_class, donut_ont_and_class]
    reasoners = ["elk", "hermit", "custom"]
    n_repetitions = 3
    results = []

    for reasoner_type in reasoners:
        for ont in ontologies:
            if not exists(ont[0]):
                print(Fore.RED + "ERROR: " + Style.RESET_ALL + f"Ontology file {ont[0]} does not exist. Skipping.")
                continue

            ontology_name = os.path.splitext(basename(ont[0]))[0]  # Extract the name without path or extension

            for i in range(n_repetitions):
                reasoner = Reasoner(ont[0], ont[1])
                runtime, n_subsumers = reasoner.get_subsumers(reasoner_type)
                
                results.append({
                    "Reasoner": reasoner_type,
                    "Ontology": ontology_name,  # Use only the ontology name
                    "Class": ont[1],
                    "Repetition": i + 1,
                    "Runtime (s)": runtime,
                    "Subsumers Found": n_subsumers
                })

                print(f"Reasoner: {reasoner_type}, Ontology: {ontology_name}, Class: {ont[1]}, "
                      f"Repetition: {i + 1}, Runtime: {runtime}s, Subsumers: {n_subsumers}")

    df = pd.DataFrame(results)
    results_file = os.path.join(results_folder, "reasoning_results.csv")
    df.to_csv(results_file, index=False)

    print(f"All results saved in {results_file}.")
