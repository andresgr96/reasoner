#! /usr/bin/python
import sys
from itertools import combinations
from py4j.java_gateway import JavaGateway
from colorama import Fore, Back, Style
from os.path import exists
import argparse

class EL_Reasoner:
    def __init__(self, ONTOLOGY, CLASS_NAME):
        self.ontology = ONTOLOGY
        self.conceptNames = ontology.getConceptNames()
        self.class_name = CLASS_NAME
        self.tbox = self.ontology.tbox()
        self.axioms = self.tbox.getAxioms()
        self.allConcepts = ontology.getSubConcepts()
        self.elFactory = gateway.getELFactory()
        self.change = True
        self.foundTop = False

        #init the GCI subsumers list
        self.gciList = list()
        for concept in self.conceptNames:
            if str(concept).startswith('"') and str(concept).endswith('"'):
                self.class_name = str('"' + CLASS_NAME + '"') 
                break
                if not(str(concept).startswith('"') and str(concept).endswith('"')):
                    self.class_name = CLASS_NAME.replace('"', '')
                break

        self.conceptD = self.elFactory.getConceptName("d") 
        conceptB = self.elFactory.getConceptName(self.class_name)
        self.gciList.append(self.elFactory.getGCI(self.conceptD,conceptB))     

    def andRule2(self):
        for combo in combinations(self.gciList, 2):
            conceptA = self.elFactory.getConceptName(str(combo[0].rhs()))
            conceptA = combo[0].rhs()
            conceptB = self.elFactory.getConceptName(str(combo[1].rhs()))
            conceptB = combo[1].rhs()
            newGci1 = self.elFactory.getGCI(self.conceptD, self.elFactory.getConjunction(combo[1].rhs(), combo[0].rhs()))
            newGci2 = self.elFactory.getGCI(self.conceptD, self.elFactory.getConjunction(combo[0].rhs(), combo[1].rhs()))
            
            if conceptA in self.allConcepts and conceptB in self.allConcepts and (newGci1 not in self.gciList or 
                                                                                  newGci2 not in self.gciList):
                if newGci1 not in self.gciList:
                    self.gciList.append(newGci1)
                    self.change = True
                if newGci2 not in self.gciList:
                    self.gciList.append(newGci2)
                    self.change = True

    def TRule(self):
        if not self.foundTop:
            for concept in self.allConcepts:
                conceptType = concept.getClass().getSimpleName()
                if(conceptType == "TopConcept$"):
                    top = self.elFactory.getTop()
                    conceptB = self.elFactory.getConceptName(formatter.format(top))
                    self.gciList.append(self.elFactory.getGCI(self.conceptD,conceptB))
                    self.foundTop = True
                    self.change = True 

    def andRule1(self, gci):
        conceptType = gci.rhs().getClass().getSimpleName()
        if(conceptType == "ConceptConjunction"):
            for concept in gci.rhs().getConjuncts():
                conceptB = self.elFactory.getConceptName(formatter.format(concept))
                conceptB = concept
                newGci = self.elFactory.getGCI(self.conceptD,conceptB)
                if(newGci not in self.gciList):
                    self.gciList.append(newGci)
                    self.change = True     

    def eRule1(self, axiom, gci):
        axiomType = axiom.getClass().getSimpleName() 
        conceptTypeGci = gci.rhs().getClass().getSimpleName()
        if(axiomType == "GeneralConceptInclusion" and conceptTypeGci == "ExistentialRoleRestriction"):
            conceptType = axiom.rhs().getClass().getSimpleName()
            if(axiom.lhs() == gci.rhs().filler() and conceptType == "ConceptName"):
                existential = self.elFactory.getExistentialRoleRestriction(self.elFactory.getRole(str(gci.rhs().role())), axiom.rhs())
                newGci = self.elFactory.getGCI(self.conceptD,existential)
                if(newGci not in self.gciList):
                    self.gciList.append(newGci)
                    self.change = True

    def checkInferenceInTbox(self,axiom,gci):
        axiomType = axiom.getClass().getSimpleName() 
        if(axiomType == "GeneralConceptInclusion" and formatter.format(axiom.lhs()) == formatter.format(gci.rhs())):
            conceptType = axiom.rhs().getClass().getSimpleName()
            if(conceptType == "ExistentialRoleRestriction"):
                conceptB = self.elFactory.getExistentialRoleRestriction(axiom.rhs().role(), axiom.rhs().filler())
            elif(conceptType == "ConceptName" or conceptType == "ConceptConjunction"):
                conceptB = self.elFactory.getConceptName(formatter.format(axiom.rhs()))
            else:
                return
            conceptB = axiom.rhs()
            newGci = self.elFactory.getGCI(self.conceptD,conceptB)
            axiomType = conceptB.getClass().getSimpleName() 
            if newGci not in self.gciList:
                self.gciList.append(newGci)
                self.change = True
    
    def checkEquivalenceInTbox(self,axiom,gci):
        axiomType = axiom.getClass().getSimpleName() 
        if(axiomType == "EquivalenceAxiom"):
            conceptList = list(axiom.getConcepts())
            conceptCounter = 0
            for concept in axiom.getConcepts():
                conceptType = concept.getClass().getSimpleName()
                if(formatter.format(concept) == formatter.format(gci.rhs()) and  
                    (conceptType == "ExistentialRoleRestriction" or conceptType == "ConceptName" or 
                        conceptType == "ConceptConjunction")):
                    conceptInverse = int(not(conceptCounter))
                
                    conceptB = self.elFactory.getConceptName(formatter.format(conceptList[conceptInverse]))
                    conceptB = conceptList[conceptInverse]
                    newGci = self.elFactory.getGCI(self.conceptD,conceptB)
                    if newGci not in self.gciList:
                        self.gciList.append(newGci)
                        self.change = True
                conceptCounter+=1

    def getSubsumers(self, args):
        if args.reasoner == 'elk':
            elk = gateway.getELKReasoner()
            classSubsumers = self.elFactory.getConceptName(self.class_name)

            print("Using ELK reasoner:")
            elk.setOntology(ontology)
            subsumers = elk.getSubsumers(classSubsumers)

            subsumers_string = subsumers.toString()
            subsumers_list = subsumers_string.strip("[]").split(',')
            for element in subsumers_list:
                clean_element = element.strip().strip('"')
                print(clean_element)

            print("(", len(subsumers), " in total)")

        elif args.reasoner == 'hermit':
            hermit = gateway.getHermiTReasoner()
            hermit.setOntology(ontology)
            class_subsumers = self.elFactory.getConceptName(self.class_name)

            print("Using HermiT reasoner:")
            subsumers = hermit.getSubsumers(class_subsumers)

            subsumers_string = subsumers.toString()
            subsumers_list = subsumers_string.strip("[]").split(',')
            for element in subsumers_list:
                clean_element = element.strip().strip('"')
                print(clean_element)

            print("(", len(subsumers), " in total)")
        else:
            while self.change:
                self.change = False
                self.andRule2()
                self.TRule()

                for gci in self.gciList:
                    self.andRule1(gci)
                    for axiom in self.axioms:
                        self.eRule1(axiom,gci)
                        self.checkInferenceInTbox(axiom,gci)
                        self.checkEquivalenceInTbox(axiom,gci)
        


           #print("Using our reasoner:")

            conceptCounter = 0
            for gci in self.gciList:
                conceptType = gci.rhs().getClass().getSimpleName()
                if(conceptType == "ConceptName" or conceptType == "TopConcept$"):
                    finalName = formatter.format(gci.rhs())
                    if str(finalName).startswith('"') and str(finalName).endswith('"'):
                        finalName = finalName.replace('"', '')
                    conceptCounter += 1
                    print(finalName)

            # print("(",conceptCounter," in total)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EL Reasoner group 2')


    parser.add_argument('--reasoner', choices=['elk', 'hermit'], default='our reasoner',
                        help='Choose the reasoner (elk, hermit, our)')
    parser.add_argument("ONTOLOGY")
    parser.add_argument("CLASS_NAME")

    args = parser.parse_args()
 
    CLASS_NAME = args.CLASS_NAME
    ONTOLOGY_FILE = args.ONTOLOGY

    #Check if the ontology file exists in current dir
    file_exists = exists(ONTOLOGY_FILE)
    if(not(file_exists)):
        print(Fore.RED + "ERROR: " + Style.RESET_ALL + "The ontology file does not exist. Please check parameters and/or if file exists")
        exit(0)


    print(f"Setting up Java gateway")
    # connect to the java gateway of dl4python
    gateway = JavaGateway()
    parser = gateway.getOWLParser()
    formatter = gateway.getSimpleDLFormatter()

    print(f"Loading ontology {ONTOLOGY_FILE}...")
    ontology = parser.parseFile(ONTOLOGY_FILE)
    gateway.convertToBinaryConjunctions(ontology)

    print(f"Running Reasoner...")
    reasoner = EL_Reasoner(ontology, CLASS_NAME)

    print(f"Retriving subsumers for target class: {CLASS_NAME}")
    print()
    print(f"Subsumers found:")
    reasoner.getSubsumers(args)