import sys
from itertools import combinations
from py4j.java_gateway import JavaGateway
import time

class Reasoner:
    def __init__(self, ONTOLOGY, CLASS_NAME):
        self.gateway = JavaGateway()
        self.parser = self.gateway.getOWLParser()
        self.formatter = self.gateway.getSimpleDLFormatter()
        self.ontology = self.parser.parseFile(ONTOLOGY)
        self.gateway.convertToBinaryConjunctions(self.ontology)
        self.concept_names = self.ontology.getConceptNames()
        self.class_name = CLASS_NAME
        self.tbox = self.ontology.tbox()
        self.axioms = self.tbox.getAxioms()
        self.concepts = self.ontology.getSubConcepts()
        self.el_fact = self.gateway.getELFactory()
        self.change = True
        self.if_top = False
        self.gci_list = list()
        self.init_concepts()
  

    def init_concepts(self):
        for concept in self.concept_names:
            if str(concept).startswith('"') and str(concept).endswith('"'):
                self.class_name = str(f'"{self.class_name}"') 
                break

        self.d = self.el_fact.getConceptName("d") 
        b = self.el_fact.getConceptName(self.class_name)
        self.gci_list.append(self.el_fact.getGCI(self.d,b))  
         
    def conjuction_two(self):
        for combination in combinations(self.gci_list, 2):
            a = self.el_fact.getConceptName(str(combination[0].rhs()))
            a = combination[0].rhs()
            b = self.el_fact.getConceptName(str(combination[1].rhs()))
            b = combination[1].rhs()
            gci_one = self.el_fact.getGCI(self.d, self.el_fact.getConjunction(combination[1].rhs(), combination[0].rhs()))
            gci_two = self.el_fact.getGCI(self.d, self.el_fact.getConjunction(combination[0].rhs(), combination[1].rhs()))
            
            if a in self.concepts and b in self.concepts and (gci_one not in self.gci_list or 
                                                                                  gci_two not in self.gci_list):
                if gci_one not in self.gci_list:
                    self.gci_list.append(gci_one)
                    self.change = True
                if gci_two not in self.gci_list:
                    self.gci_list.append(gci_two)
                    self.change = True

    def top_rule(self):
        if not self.if_top:
            for concept in self.concepts:
                type = concept.getClass().getSimpleName()
                if(type == "TopConcept$"):
                    top = self.el_fact.getTop()
                    b = self.el_fact.getConceptName(self.formatter.format(top))
                    self.gci_list.append(self.el_fact.getGCI(self.d,b))
                    self.if_top = True
                    self.change = True 

    def conjuction_one(self, gci):
        type = gci.rhs().getClass().getSimpleName()
        if(type == "ConceptConjunction"):
            for concept in gci.rhs().getConjuncts():
                b = self.el_fact.getConceptName(self.formatter.format(concept))
                b = concept
                new_gci = self.el_fact.getGCI(self.d,b)
                if(new_gci not in self.gci_list):
                    self.gci_list.append(new_gci)
                    self.change = True     

    def existential_one(self, axiom, gci):
        axiom_type = axiom.getClass().getSimpleName() 
        gci_type = gci.rhs().getClass().getSimpleName()
        if(axiom_type == "GeneralConceptInclusion" and gci_type == "ExistentialRoleRestriction"):
            type = axiom.rhs().getClass().getSimpleName()
            if(axiom.lhs() == gci.rhs().filler() and type == "ConceptName"):
                existential = self.el_fact.getExistentialRoleRestriction(self.el_fact.getRole(str(gci.rhs().role())), axiom.rhs())
                new_gci = self.el_fact.getGCI(self.d,existential)
                if(new_gci not in self.gci_list):
                    self.gci_list.append(new_gci)
                    self.change = True

    def top_inference(self,axiom,gci):
        axiom_type = axiom.getClass().getSimpleName() 
        if(axiom_type == "GeneralConceptInclusion" and self.formatter.format(axiom.lhs()) == self.formatter.format(gci.rhs())):
            type = axiom.rhs().getClass().getSimpleName()
            if(type == "ExistentialRoleRestriction"):
                b = self.el_fact.getExistentialRoleRestriction(axiom.rhs().role(), axiom.rhs().filler())
            elif(type == "ConceptName" or type == "ConceptConjunction"):
                b = self.el_fact.getConceptName(self.formatter.format(axiom.rhs()))
            else:
                return
            b = axiom.rhs()
            new_gci = self.el_fact.getGCI(self.d,b)
            axiom_type = b.getClass().getSimpleName() 
            if new_gci not in self.gci_list:
                self.gci_list.append(new_gci)
                self.change = True
    
    def top_equivalence(self,axiom,gci):
        axiom_type = axiom.getClass().getSimpleName() 
        if(axiom_type == "EquivalenceAxiom"):
            concepts = list(axiom.getConcepts())
            n_concepts = 0
            for concept in axiom.getConcepts():
                type = concept.getClass().getSimpleName()
                if(self.formatter.format(concept) == self.formatter.format(gci.rhs()) and  
                    (type == "ExistentialRoleRestriction" or type == "ConceptName" or 
                        type == "ConceptConjunction")):
                    conceptInverse = int(not(n_concepts))
                
                    b = self.el_fact.getConceptName(self.formatter.format(concepts[conceptInverse]))
                    b = concepts[conceptInverse]
                    new_gci = self.el_fact.getGCI(self.d,b)
                    if new_gci not in self.gci_list:
                        self.gci_list.append(new_gci)
                        self.change = True
                n_concepts+=1

    def get_subsumers(self, reasoner):
        if reasoner in ['elk', 'hermit']:
            return self.ont_subsumers(reasoner)
        else:
            return self.custom_subsumers()

    def ont_subsumers(self, which_reason):
        reasoner = self.gateway.getHermiTReasoner() if which_reason == "hermit" else self.gateway.getELKReasoner()
        reasoner.setOntology(self.ontology)
        class_subsumers = self.el_fact.getConceptName(self.class_name)
        subsumers = reasoner.getSubsumers(class_subsumers)

        subsumers_string = subsumers.toString()
        subsumers_list = subsumers_string.strip("[]").split(',')
        for element in subsumers_list:
            clean_element = element.strip().strip('"')
            print(clean_element)

    def custom_subsumers(self):
        while self.change:
            self.change = False
            self.conjuction_two()
            self.top_rule()

            for gci in self.gci_list:
                self.conjuction_one(gci)
                for axiom in self.axioms:
                    self.existential_one(axiom,gci)
                    self.top_inference(axiom,gci)
                    self.top_equivalence(axiom,gci)

        n_concepts = 0
        for gci in self.gci_list:
            type = gci.rhs().getClass().getSimpleName()
            if(type == "ConceptName" or type == "TopConcept$"):
                concept_name = self.formatter.format(gci.rhs())
                if str(concept_name).startswith('"') and str(concept_name).endswith('"'):
                    concept_name = concept_name.replace('"', '')
                n_concepts += 1
                print(concept_name)


