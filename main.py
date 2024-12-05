import argparse
from reasoner_class import Reasoner
from colorama import Fore, Back, Style
from os.path import exists
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EL Reasoner group 2')


    parser.add_argument('--reasoner', choices=['elk', 'hermit'], default='our reasoner',
                        help='Choose the reasoner (elk, hermit, our)')
    parser.add_argument("ONTOLOGY")
    parser.add_argument("CLASS_NAME")

    args = parser.parse_args()
 
    file_exists = exists(args.ONTOLOGY)
    if(not(file_exists)):
        print(Fore.RED + "ERROR: " + Style.RESET_ALL + "The ontology file does not exist. Please check parameters and/or if file exists")
        exit(0)



    reasoner = Reasoner(args.ONTOLOGY, args.CLASS_NAME)
    reasoner.getSubsumers(args)
