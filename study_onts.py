#! /usr/bin/python
import os
from os.path import exists, basename, join, splitext

from py4j.java_gateway import JavaGateway

# Connect to the Java gateway of dl4python
gateway = JavaGateway()
parser = gateway.getOWLParser()
formatter = gateway.getSimpleDLFormatter()

# Directory containing ontologies
ontologies_dir = "./ontologies/"

if not exists(ontologies_dir):
    print(f"Directory {ontologies_dir} does not exist. Please check the path.")
    exit(1)

for file in os.listdir(ontologies_dir):
    ontology_path = join(ontologies_dir, file)
    
    if not file.endswith((".owl", ".owl.xml")):
        print(f"Skipping non-ontology file: {file}")
        continue

    ontology_name = splitext(basename(file))[0]
    print(f"\nStats for {ontology_name}:")
    
    try:
        ontology = parser.parseFile(ontology_path)
    except Exception as e:
        print(f"Error loading ontology {file}: {e}")
        continue

    # Convert ontology to binary conjunctions
    gateway.convertToBinaryConjunctions(ontology)
    # get the TBox axioms
    tbox = ontology.tbox()
    axioms = tbox.getAxioms()
    all_concepts = ontology.getSubConcepts()
    concept_names = ontology.getConceptNames()

    print(f"There are {len(axioms)} axioms occurring in the ontology.")
    print(f"There are {len(all_concepts)} concepts occurring in the ontology.")
    print(f"There are {len(concept_names)} concept names occurring in the ontology.")
    # print("Concept names:")
    # for name in concept_names:
    #     print(f"- {formatter.format(name)}")
