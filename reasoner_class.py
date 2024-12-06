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
        self.concept_names = set(self.ontology.getConceptNames())  
        self.class_name = CLASS_NAME
        self.tbox = self.ontology.tbox()
        self.axioms = self.tbox.getAxioms()
        self.concepts = set(self.ontology.getSubConcepts())  
        self.el_fact = self.gateway.getELFactory()
        self.change = True
        self.if_top = False
        self.gci_set = set()  
        self.init_concepts()
  
    def init_concepts(self):
        """Initialize the GCI set with the main class and a placeholder concept."""
        for concept in self.concept_names:
            if str(concept).startswith('"') and str(concept).endswith('"'):
                self.class_name = str(f'"{self.class_name}"') 
                break

        self.d = self.el_fact.getConceptName("d") 
        b = self.el_fact.getConceptName(self.class_name)
        self.gci_set.add(self.el_fact.getGCI(self.d, b)) 

    def top_rule(self):
        """Add the TopConcept$ if not already present."""
        if not self.if_top:
            for concept in self.concepts:
                if concept.getClass().getSimpleName() == "TopConcept$":
                    top = self.el_fact.getTop()
                    b = self.el_fact.getConceptName(self.formatter.format(top))
                    self.gci_set.add(self.el_fact.getGCI(self.d, b))
                    self.if_top = True
                    self.change = True
                    break

    def conjuction_one(self, gci):
        """Break down a GCI containing a conjunction into individual GCIs."""
        if gci.rhs().getClass().getSimpleName() == "ConceptConjunction":
            for concept in gci.rhs().getConjuncts():
                new_gci = self.el_fact.getGCI(self.d, concept)
                if new_gci not in self.gci_set:
                    self.gci_set.add(new_gci)
                    self.change = True     

    def conjuction_two(self):
        """Combine every two GCIs in gci_set and add their conjunctions to gci_set."""
        current_gc_list = list(self.gci_set) # Combinations run faster in lists
        for combination in combinations(current_gc_list, 2):
            gci_one = self.el_fact.getGCI(self.d, self.el_fact.getConjunction(combination[0].rhs(), combination[1].rhs()))
            gci_two = self.el_fact.getGCI(self.d, self.el_fact.getConjunction(combination[1].rhs(), combination[0].rhs()))
            a = combination[0].rhs()
            b = combination[1].rhs()

            if a in self.concepts and b in self.concepts and (gci_one not in self.gci_set or gci_two not in self.gci_set):
                if gci_one not in self.gci_set:
                    self.gci_set.add(gci_one)
                    self.change = True
                if gci_two not in self.gci_set:
                    self.gci_set.add(gci_two)
                    self.change = True   

    def existential_one(self, axiom, gci):
        """Handle existential role restrictions in axioms."""
        if (axiom.getClass().getSimpleName() == "GeneralConceptInclusion" and
            gci.rhs().getClass().getSimpleName() == "ExistentialRoleRestriction" and
            axiom.lhs() == gci.rhs().filler() and
            axiom.rhs().getClass().getSimpleName() == "ConceptName"):
            
            existential = self.el_fact.getExistentialRoleRestriction(
                self.el_fact.getRole(str(gci.rhs().role())), axiom.rhs()
            )
            new_gci = self.el_fact.getGCI(self.d, existential)
            if new_gci not in self.gci_set:
                self.gci_set.add(new_gci)
                self.change = True

    def top_inference(self, axiom, gci):
        """Infer new GCIs from axioms in the TBox."""
        if (axiom.getClass().getSimpleName() == "GeneralConceptInclusion" and
            self.formatter.format(axiom.lhs()) == self.formatter.format(gci.rhs())):
            
            rhs = axiom.rhs()
            if rhs.getClass().getSimpleName() == "ExistentialRoleRestriction":
                new_rhs = self.el_fact.getExistentialRoleRestriction(rhs.role(), rhs.filler())
            elif rhs.getClass().getSimpleName() in ("ConceptName", "ConceptConjunction"):
                new_rhs = self.el_fact.getConceptName(self.formatter.format(rhs))
            else:
                return
            
            new_gci = self.el_fact.getGCI(self.d, new_rhs)
            if new_gci not in self.gci_set:
                self.gci_set.add(new_gci)
                self.change = True

    def top_equivalence(self, axiom, gci):
        """Handle equivalence axioms."""
        if axiom.getClass().getSimpleName() == "EquivalenceAxiom":
            concepts = list(axiom.getConcepts())
            for concept in concepts:
                if (self.formatter.format(concept) == self.formatter.format(gci.rhs()) and
                    concept.getClass().getSimpleName() in ("ExistentialRoleRestriction", "ConceptName", "ConceptConjunction")):
                    for inverse in concepts:
                        if inverse != concept:
                            break
  
                    new_gci = self.el_fact.getGCI(self.d, inverse)
                    if new_gci not in self.gci_set:
                        self.gci_set.add(new_gci)
                        self.change = True

    def get_subsumers(self, reasoner):
        """Get subsumers for the given reasoner."""
        start_time = time.time()
        if reasoner in ['elk', 'hermit']:
            n_subsumers = self.ont_subsumers(reasoner)
        else:
            n_subsumers = self.custom_subsumers()

        runtime = f"{time.time() - start_time:.2f}"
        return runtime, n_subsumers

    def ont_subsumers(self, which_reason):
        """Retrieve subsumers using ELK or HermiT reasoners."""
        reasoner = self.gateway.getHermiTReasoner() if which_reason == "hermit" else self.gateway.getELKReasoner()
        reasoner.setOntology(self.ontology)
        class_subsumers = self.el_fact.getConceptName(self.class_name)
        subsumers = reasoner.getSubsumers(class_subsumers)

        subsumers_list = subsumers.toString().strip("[]").split(',')
        for element in sorted(subsumers_list):
            print(element.strip().strip('"'))
        return len(subsumers_list)

    def custom_subsumers(self):
        """Retrieve subsumers using the custom reasoner."""
        processed_gci = set()  
        concept_names = set()  

        while self.change:
            self.change = False
            self.conjuction_two()  
            self.top_rule()  

            for gci in list(self.gci_set):  
                if gci in processed_gci:
                    continue
                processed_gci.add(gci)  
                self.conjuction_one(gci)
                for axiom in self.axioms:
                    self.existential_one(axiom, gci)
                    self.top_inference(axiom, gci)
                    self.top_equivalence(axiom, gci)

                if gci.rhs().getClass().getSimpleName() in ("ConceptName", "TopConcept$"):
                    concept_name = self.formatter.format(gci.rhs()).strip('"')
                    concept_names.add(concept_name)

        for name in sorted(concept_names):  # Sorting for easier cross-checking
            print(name)
        return len(concept_names)
